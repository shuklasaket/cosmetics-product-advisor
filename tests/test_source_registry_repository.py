"""US-034: atomic SQLite persistence for the approved source registry."""

from pathlib import Path

import pytest
from test_refresh_contracts import approved_source

from repositories import catalog as storage
from repositories.migrations import SCHEMA_V1
from repositories.source_registry import SourceRegistryRepository, SourceRegistryStorageError
from schemas.refresh import SourceRegistry


def registry(*, source_id: str = "open-beauty-facts") -> SourceRegistry:
    return SourceRegistry(
        version="approved-sources-v1",
        sources=(approved_source(source_id=source_id),),
    )


def test_registry_round_trip_survives_reopen_and_catalog_migration(tmp_path: Path) -> None:
    path = tmp_path / "catalog.db"
    storage.migrate(path)
    repo = SourceRegistryRepository(path)
    assert repo.read() == SourceRegistry(version="approved-sources-v1", sources=())
    repo.replace(registry())
    assert SourceRegistryRepository(path).read() == registry()
    with storage.connection(path, readonly=True) as con:
        assert con.execute("PRAGMA user_version").fetchone()[0] == storage.SCHEMA_VERSION


def test_v1_catalog_upgrades_with_backup_and_preserves_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_catalog_contracts import catalog

    from schemas.catalog import CatalogEnvelope

    path = tmp_path / "upgrade.db"
    with monkeypatch.context() as patch:
        patch.setattr(storage, "MIGRATIONS", (SCHEMA_V1,))
        patch.setattr(storage, "SCHEMA_VERSION", 1)
        storage.migrate(path)
        original = CatalogEnvelope.model_validate(catalog())
        storage.CatalogRepository(path).save(original)
    backup = storage.migrate(path)
    assert backup is not None
    assert storage.CatalogRepository(path).read() == original
    with monkeypatch.context() as patch:
        patch.setattr(storage, "MIGRATIONS", (SCHEMA_V1,))
        patch.setattr(storage, "SCHEMA_VERSION", 1)
        assert storage.CatalogRepository(backup).read() == original
    SourceRegistryRepository(path).replace(registry())
    assert SourceRegistryRepository(path).read() == registry()


def test_invalid_or_failed_replace_preserves_last_valid_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "registry.db"
    storage.migrate(path)
    repo = SourceRegistryRepository(path)
    original = registry()
    repo.replace(original)
    forged = original.model_copy(update={"version": "unsupported"})
    with pytest.raises(SourceRegistryStorageError, match="preserved"):
        repo.replace(forged)
    with storage.connection(path) as con:
        con.execute(
            "CREATE TRIGGER fail_registry BEFORE INSERT ON approved_sources "
            "BEGIN SELECT RAISE(ABORT, 'injected'); END"
        )
    with pytest.raises(SourceRegistryStorageError, match="preserved"):
        repo.replace(registry(source_id="replacement"))
    assert repo.read() == original


def test_registry_rejects_duplicate_ids_before_write(tmp_path: Path) -> None:
    path = tmp_path / "duplicates.db"
    storage.migrate(path)
    repo = SourceRegistryRepository(path)
    original = registry()
    repo.replace(original)
    with pytest.raises(ValueError, match="Duplicate"):
        SourceRegistry(
            version="approved-sources-v1",
            sources=(approved_source(), approved_source()),
        )
    assert repo.read() == original


def test_missing_or_old_database_is_not_modified(tmp_path: Path) -> None:
    missing = tmp_path / "missing.db"
    with pytest.raises(SourceRegistryStorageError):
        SourceRegistryRepository(missing).read()
    assert not missing.exists()
