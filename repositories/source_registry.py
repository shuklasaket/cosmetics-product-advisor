"""Atomic SQLite persistence for the approved retrieval-source registry."""

import json
import sqlite3
from pathlib import Path

from repositories.catalog import SCHEMA_VERSION, _version, connection
from schemas.refresh import SourceRegistry


class SourceRegistryStorageError(Exception):
    """Sanitized registry-storage diagnostic."""


def _read_registry(con: sqlite3.Connection) -> SourceRegistry:
    sources = [
        json.loads(row[0])
        for row in con.execute("SELECT payload FROM approved_sources ORDER BY source_id")
    ]
    return SourceRegistry.model_validate({"version": "approved-sources-v1", "sources": sources})


class SourceRegistryRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> SourceRegistry:
        try:
            with connection(self.path, readonly=True) as con:
                con.execute("BEGIN")
                if _version(con) != SCHEMA_VERSION:
                    raise SourceRegistryStorageError(
                        "Approved source registry upgrade required. Run catalog migration first."
                    )
                return _read_registry(con)
        except SourceRegistryStorageError:
            raise
        except (sqlite3.Error, OSError, ValueError):
            raise SourceRegistryStorageError(
                "Approved source registry is unavailable or invalid. Restore a verified backup."
            ) from None

    def replace(self, registry: SourceRegistry) -> None:
        try:
            value = SourceRegistry.model_validate_json(registry.model_dump_json())
            with connection(self.path) as con:
                con.execute("BEGIN IMMEDIATE")
                if _version(con) != SCHEMA_VERSION:
                    raise SourceRegistryStorageError(
                        "Approved source registry upgrade required. Run catalog migration first."
                    )
                con.execute("DELETE FROM approved_sources")
                con.executemany(
                    "INSERT INTO approved_sources(payload) VALUES (?)",
                    [(source.model_dump_json(),) for source in value.sources],
                )
                if _read_registry(con) != value:
                    raise SourceRegistryStorageError(
                        "Approved source registry verification failed."
                    )
                con.execute("COMMIT")
        except SourceRegistryStorageError:
            raise
        except (sqlite3.Error, OSError, ValueError):
            raise SourceRegistryStorageError(
                "Approved source registry write rejected. Previous registry was preserved."
            ) from None
