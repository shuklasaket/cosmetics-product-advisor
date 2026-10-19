"""SQLite evidence storage and read-only queries; no sensitive request persistence."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from repositories.migrations import MIGRATIONS
from schemas.catalog import CatalogEnvelope
from schemas.search import CatalogFilters

APPLICATION_ID = 0x43504131  # CPA1
SCHEMA_VERSION = len(MIGRATIONS)
TABLES = ("products", "sources", "observations", "resolutions")


class CatalogStorageError(Exception):
    """Fixed public diagnostics: never include SQL, source payloads or private paths."""


@contextmanager
def connection(
    path: Path, *, create: bool = False, readonly: bool = False
) -> Iterator[sqlite3.Connection]:
    """Explicit SQLite autocommit with caller-owned BEGIN/COMMIT; close on every path."""
    mode = "ro" if readonly else ("rwc" if create else "rw")
    con = sqlite3.connect(f"{path.resolve().as_uri()}?mode={mode}", uri=True, autocommit=True)
    try:
        con.execute("PRAGMA foreign_keys = ON")
        yield con
    finally:
        if con.in_transaction:
            con.execute("ROLLBACK")
        con.close()


def _version(con: sqlite3.Connection, *, initializing: bool = False) -> int:
    version: int = con.execute("PRAGMA user_version").fetchone()[0]
    application: int = con.execute("PRAGMA application_id").fetchone()[0]
    tables = con.execute("SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
    if initializing and version == 0 and application == 0 and not tables:
        return 0
    if application != APPLICATION_ID or not 1 <= version <= SCHEMA_VERSION:
        raise CatalogStorageError(
            "Unsupported catalog schema. Use a compatible backup or application."
        )
    return version


def _read(con: sqlite3.Connection) -> CatalogEnvelope:
    if (
        con.execute("PRAGMA quick_check").fetchall() != [("ok",)]
        or con.execute("PRAGMA foreign_key_check").fetchall()
    ):
        raise CatalogStorageError("Invalid catalog database. Restore a verified backup.")
    data = {
        table: [
            json.loads(row[0]) for row in con.execute(f"SELECT payload FROM {table} ORDER BY rowid")
        ]
        for table in TABLES
    }
    value = CatalogEnvelope.model_validate({"contract_version": "catalog-v1", **data})
    expected = {
        (r.product_id, r.field_name, eid) for r in value.resolutions for eid in r.evidence_ids
    }
    actual = set(con.execute("SELECT product_id, field_name, evidence_id FROM resolution_evidence"))
    if actual != expected:
        raise CatalogStorageError("Invalid catalog evidence links. Restore a verified backup.")
    return value


def _backup(con: sqlite3.Connection, path: Path) -> Path:
    directory = path.parent / f"{path.name}.backups"
    directory.mkdir(parents=True, exist_ok=True)
    destination = (
        directory / f"v{con.execute('PRAGMA user_version').fetchone()[0]}-{uuid4().hex}.db"
    )
    with connection(destination, create=True) as target:
        con.backup(target)
    return destination


def migrate(path: Path) -> Path | None:
    """Initialize empty storage or apply ordered forward migrations; return pre-upgrade backup."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with connection(path, create=True) as con:
            version = _version(con, initializing=True)
            if version:
                _read(con)
            if version == SCHEMA_VERSION:
                return None
            backup = _backup(con, path) if version else None
            con.execute("BEGIN EXCLUSIVE")
            # Recheck after acquiring the write lock; never migrate a concurrently changed schema.
            if _version(con, initializing=True) != version:
                raise CatalogStorageError(
                    "Catalog changed during migration. Retry with the app stopped."
                )
            for index in range(version, SCHEMA_VERSION):
                for statement in MIGRATIONS[index]:
                    con.execute(statement)
                con.execute(f"PRAGMA user_version = {index + 1}")
            con.execute(f"PRAGMA application_id = {APPLICATION_ID}")
            _read(con)
            con.execute("COMMIT")
            return backup
    except (sqlite3.Error, OSError, ValueError):
        raise CatalogStorageError(
            "Catalog migration failed. Keep the database and restore a backup."
        ) from None


class CatalogRepository:
    """Complete catalog snapshots. Retain old identities, sources and observations unchanged."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> CatalogEnvelope:
        try:
            with connection(self.path, readonly=True) as con:
                con.execute("BEGIN")
                if _version(con) != SCHEMA_VERSION:
                    raise CatalogStorageError(
                        "Catalog upgrade required. Back up and run migrate first."
                    )
                return _read(con)
        except (sqlite3.Error, OSError, ValueError):
            raise CatalogStorageError(
                "Catalog unavailable or invalid. Check the file or restore a backup."
            ) from None

    def _query(self, sql: str, parameters: tuple[str, ...]) -> CatalogEnvelope:
        """Validate and query one read snapshot, returning only matching evidence/history."""
        try:
            with connection(self.path, readonly=True) as con:
                con.execute("BEGIN")
                if _version(con) != SCHEMA_VERSION:
                    raise CatalogStorageError(
                        "Catalog upgrade required. Back up and run migrate first."
                    )
                snapshot = _read(con)
                # JSON integer text avoids SQLite's REAL conversion above signed 64-bit range.
                con.create_function(
                    "paise_at_most",
                    2,
                    lambda price, ceiling: price != "null" and int(price) <= int(ceiling),
                    deterministic=True,
                )
                product_ids = [row[0] for row in con.execute(sql, parameters)]
                products = {p.product_id: p for p in snapshot.products}
                selected = set(product_ids)
                observations = tuple(o for o in snapshot.observations if o.product_id in selected)
                source_ids = {o.source_id for o in observations}
                return CatalogEnvelope(
                    contract_version="catalog-v1",
                    products=tuple(products[pid] for pid in product_ids),
                    sources=tuple(s for s in snapshot.sources if s.source_id in source_ids),
                    observations=observations,
                    resolutions=tuple(r for r in snapshot.resolutions if r.product_id in selected),
                )
        except (sqlite3.Error, OSError, ValueError):
            raise CatalogStorageError(
                "Catalog unavailable or invalid. Check the file or restore a backup."
            ) from None

    def search(self, filters: CatalogFilters) -> CatalogEnvelope:
        """Exact category, selected India availability and inclusive integer-paise ceiling."""
        value = CatalogFilters.model_validate(filters.model_dump(warnings=False))
        return self._query(
            """SELECT p.product_id FROM products AS p
            WHERE p.category = ? AND EXISTS (
                SELECT 1 FROM resolutions AS r
                JOIN resolution_evidence AS re USING (product_id, field_name)
                JOIN observations AS o USING (evidence_id, product_id, field_name)
                JOIN json_each(o.payload, '$.value') AS country
                WHERE r.product_id = p.product_id AND r.field_name = 'availability'
                    AND r.status = 'selected' AND country.value = ? COLLATE BINARY
            ) AND EXISTS (
                SELECT 1 FROM resolutions AS r
                JOIN resolution_evidence AS re USING (product_id, field_name)
                JOIN observations AS o USING (evidence_id, product_id, field_name)
                WHERE r.product_id = p.product_id AND r.field_name = 'price_paise'
                    AND r.status = 'selected' AND paise_at_most(o.payload -> '$.value', ?)
            ) ORDER BY p.name COLLATE BINARY, p.product_id COLLATE BINARY""",
            (value.category, value.country, str(value.budget_paise)),
        )

    def detail(self, product_id: str) -> CatalogEnvelope:
        """A catalog-v1 subset or an empty catalog for an absent exact ID."""
        return self._query("SELECT product_id FROM products WHERE product_id = ?", (product_id,))

    def save(self, envelope: CatalogEnvelope, *, expected: CatalogEnvelope | None = None) -> None:
        try:
            # Revalidate even deliberately constructed/copied Pydantic instances.
            value = CatalogEnvelope.model_validate_json(envelope.model_dump_json())
            with connection(self.path) as con:
                con.execute("BEGIN IMMEDIATE")
                if _version(con) != SCHEMA_VERSION:
                    raise CatalogStorageError(
                        "Catalog upgrade required. Back up and run migrate first."
                    )
                current = _read(con)
                if expected is not None and current != expected:
                    raise CatalogStorageError("Catalog changed during import. Reload and retry.")
                for table, identity in (
                    ("products", "product_id"),
                    ("sources", "source_id"),
                    ("observations", "evidence_id"),
                ):
                    incoming = {
                        getattr(record, identity): record.model_dump(mode="json")
                        for record in getattr(value, table)
                    }
                    stored = {
                        row[0]: json.loads(row[1])
                        for row in con.execute(f"SELECT {identity}, payload FROM {table}")
                    }
                    if any(incoming.get(key) != payload for key, payload in stored.items()):
                        raise CatalogStorageError(
                            "Catalog history cannot be removed or rewritten. Retain prior records."
                        )
                    for record in getattr(value, table):
                        if getattr(record, identity) not in stored:
                            con.execute(
                                f"INSERT INTO {table}(payload) VALUES (?)",
                                (record.model_dump_json(),),
                            )
                con.execute("DELETE FROM resolution_evidence")
                con.execute("DELETE FROM resolutions")
                for record in value.resolutions:
                    con.execute(
                        "INSERT INTO resolutions(payload) VALUES (?)", (record.model_dump_json(),)
                    )
                    con.executemany(
                        "INSERT INTO resolution_evidence VALUES (?, ?, ?)",
                        [
                            (record.product_id, record.field_name, eid)
                            for eid in record.evidence_ids
                        ],
                    )
                _read(con)
                con.execute("COMMIT")
        except (sqlite3.Error, OSError, ValueError):
            raise CatalogStorageError(
                "Catalog write rejected. Previous data was preserved."
            ) from None

    def backup(self) -> Path:
        try:
            with connection(self.path, readonly=True) as con:
                _version(con)
                _read(con)
                return _backup(con, self.path)
        except (sqlite3.Error, OSError, ValueError):
            raise CatalogStorageError(
                "Catalog backup failed. Check local storage and retry."
            ) from None


def restore(backup: Path, destination: Path) -> None:
    """Restore only into a new path; operator stops the app and switches paths explicitly."""
    try:
        CatalogRepository(backup).read()
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents accidentally overwriting a newer/last-valid database.
        with destination.open("xb"):
            pass
        with connection(backup, readonly=True) as source, connection(destination) as target:
            source.backup(target)
        CatalogRepository(destination).read()
    except (sqlite3.Error, OSError, ValueError):
        raise CatalogStorageError(
            "Restore failed. Choose a verified backup and a new destination."
        ) from None
