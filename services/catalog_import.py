"""Offline catalog-v1 import orchestration; reports never contain source payloads."""

import json
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from repositories.catalog import CatalogRepository, CatalogStorageError
from schemas.catalog import CatalogEnvelope, FactObservation, FactResolution, Product, Source
from schemas.common import Contract


@dataclass(frozen=True)
class RowIssue:
    row: str
    message: str


@dataclass(frozen=True)
class ImportReport:
    status: Literal["committed", "unchanged", "rejected", "failed"]
    accepted: int = 0
    rejected: int = 0
    unchanged: int = 0
    updated_resolutions: int = 0
    unresolved: int = 0
    committed: bool = False
    rows_known: bool = True
    issues: tuple[RowIssue, ...] = ()


MODELS: dict[str, type[Contract]] = {
    "products": Product,
    "sources": Source,
    "observations": FactObservation,
    "resolutions": FactResolution,
}


def reject(rows: dict[str, list[Any]], problems: dict[str, str]) -> ImportReport:
    labels = [
        f"{table}:{index}" for table, items in rows.items() for index in range(1, len(items) + 1)
    ]
    issues = tuple(
        RowIssue(
            label,
            problems.get(
                label, "Batch withheld. Correct the reported errors and retry the complete batch."
            ),
        )
        for label in labels
    )
    if "batch" in problems:
        issues += (RowIssue("batch", problems["batch"]),)
    return ImportReport(status="rejected", rejected=len(labels), issues=issues)


def preflight(data: object) -> CatalogEnvelope | ImportReport:
    if not isinstance(data, dict):
        return reject({}, {"batch": "Supply a catalog-v1 JSON object with all four collections."})
    rows = {table: data[table] for table in MODELS if isinstance(data.get(table), list)}
    problems: dict[str, str] = {}
    if (
        set(data) != {"contract_version", *MODELS}
        or data.get("contract_version") != "catalog-v1"
        or len(rows) != 4
    ):
        problems["batch"] = (
            "Supply only contract_version catalog-v1 and four required array collections."
        )
    valid: dict[str, list[tuple[str, Contract]]] = {table: [] for table in MODELS}
    for table, items in rows.items():
        for index, raw in enumerate(items, 1):
            label = f"{table}:{index}"
            try:
                valid[table].append((label, MODELS[table].model_validate(raw)))
            except ValidationError as error:
                problems[label] = " ".join(MODELS[table].validation_messages(error))
    products = {record.product_id for _, record in valid["products"] if isinstance(record, Product)}
    sources = {
        record.source_id: record for _, record in valid["sources"] if isinstance(record, Source)
    }
    for label, record in valid["observations"]:
        assert isinstance(record, FactObservation)
        source = sources.get(record.source_id)
        if record.product_id not in products or source is None or not source.enabled:
            problems[label] = (
                "Link to a valid product and enabled source "
                "with complete permission/reuse metadata."
            )
    if problems:
        return reject(rows, problems)
    try:
        return CatalogEnvelope.model_validate(data)
    except ValidationError:
        return reject(
            rows,
            {
                "batch": (
                    "Check duplicate IDs, exact variants, field/evidence links, "
                    "explicit resolutions and compatible verified snapshots."
                )
            },
        )


def record_key(table: str, record: Contract) -> tuple[str, ...]:
    fields = {
        "products": ("product_id",),
        "sources": ("source_id",),
        "observations": ("evidence_id",),
        "resolutions": ("product_id", "field_name"),
    }
    return tuple(getattr(record, field) for field in fields[table])


def merge(
    current: CatalogEnvelope, incoming: CatalogEnvelope, *, update_resolutions: bool
) -> tuple[CatalogEnvelope, int, int] | ImportReport:
    collections: dict[str, list[Contract]] = {}
    problems: dict[str, str] = {}
    unchanged = updated = 0
    for table in MODELS:
        existing = {record_key(table, record): record for record in getattr(current, table)}
        for index, record in enumerate(getattr(incoming, table), 1):
            key = record_key(table, record)
            prior = existing.get(key)
            if prior == record:
                unchanged += 1
            elif prior is not None:
                if table != "resolutions":
                    problems[f"{table}:{index}"] = (
                        "Existing ID has different data. Retain immutable history and use a new "
                        "evidence/source ID; review product variant mapping."
                    )
                elif not update_resolutions:
                    problems[f"{table}:{index}"] = (
                        "Stored resolution differs. Review the evidence and retry with "
                        "--update-resolutions to replace it explicitly."
                    )
                else:
                    updated += 1
            existing[key] = record
        collections[table] = list(existing.values())
    rows = {table: list(getattr(incoming, table)) for table in MODELS}
    if problems:
        return reject(rows, problems)
    try:
        combined = CatalogEnvelope.model_validate(
            {
                "contract_version": "catalog-v1",
                **{
                    table: [record.model_dump(mode="json") for record in records]
                    for table, records in collections.items()
                },
            }
        )
    except ValidationError:
        return reject(
            rows,
            {
                "batch": (
                    "Merged catalog is invalid. Review exact variant identities, "
                    "retained evidence links and compatible rating/count snapshots."
                )
            },
        )
    return combined, unchanged, updated


MAX_INPUT_BYTES = 5 * 1024 * 1024


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON member")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ValueError("Non-finite JSON number")


def failed(rows: dict[str, list[Any]] | None, message: str) -> ImportReport:
    return replace(
        reject(rows or {}, {"batch": message}), status="failed", rows_known=rows is not None
    )


def import_catalog(path: Path, database: Path, *, update_resolutions: bool = False) -> ImportReport:
    try:
        if not path.is_file():
            raise ValueError("Regular file required")
        with path.open("rb") as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("Input limit exceeded")
        data = json.loads(
            raw.decode("utf-8"),
            parse_float=Decimal,
            parse_constant=reject_constant,
            object_pairs_hook=unique_object,
        )
        result = preflight(data)
    except (OSError, ValueError, RecursionError, InvalidOperation):
        return failed(
            None,
            "Read a local UTF-8 JSON file of at most 5 MiB; fix syntax, duplicate members "
            "or non-finite numbers. Row counts unavailable.",
        )
    if isinstance(result, ImportReport):
        return result
    rows = {table: list(getattr(result, table)) for table in MODELS}
    repository = CatalogRepository(database)
    try:
        current = repository.read()
        combined = merge(current, result, update_resolutions=update_resolutions)
        if isinstance(combined, ImportReport):
            return combined
        value, unchanged, updated = combined
        count = sum(len(items) for items in rows.values())
        changed = unchanged != count
        if changed:
            repository.save(value, expected=current)
    except CatalogStorageError:
        return failed(
            rows,
            "Database read/write failed or changed during import. No import changes committed. "
            "Check the configured database, initialize/restore if needed, "
            "then retry with the app stopped.",
        )
    return ImportReport(
        status="committed" if changed else "unchanged",
        accepted=count,
        unchanged=unchanged,
        updated_resolutions=updated,
        unresolved=sum(r.status == "unresolved" for r in value.resolutions),
        committed=changed,
    )
