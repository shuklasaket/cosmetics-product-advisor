"""US-014: temporary real SQLite databases with synthetic evidence only."""

from pathlib import Path

from test_catalog_contracts import catalog

from repositories import catalog as storage
from schemas.catalog import CatalogEnvelope


def test_complete_catalog_survives_reopen(tmp_path: Path) -> None:
    path = tmp_path / "catalog.db"
    storage.migrate(path)
    value = CatalogEnvelope.model_validate(catalog())
    storage.CatalogRepository(path).save(value)
    assert storage.CatalogRepository(path).read() == value


def test_missing_database_is_not_created(tmp_path: Path) -> None:
    import pytest

    path = tmp_path / "missing.db"
    with pytest.raises(storage.CatalogStorageError):
        storage.CatalogRepository(path).read()
    assert not path.exists()


def test_history_and_explicit_resolution_survive_restart(tmp_path: Path) -> None:
    from test_catalog_contracts import observation, select

    path = tmp_path / "history.db"
    storage.migrate(path)
    data = catalog()
    storage.CatalogRepository(path).save(CatalogEnvelope.model_validate(data))
    data["observations"].append(
        observation("price_paise", 90_000, source="retailer", suffix="-new")
    )
    data["resolutions"] = [r for r in data["resolutions"] if r["field_name"] != "price_paise"]
    data["resolutions"].append(
        select("price_paise", ["e-price_paise", "e-price_paise-new"], "unresolved")
    )
    repo = storage.CatalogRepository(path)
    repo.save(CatalogEnvelope.model_validate(data))
    assert repo.read().resolved_value("synthetic-50ml", "price_paise") is None
    data["resolutions"][-1] = select("price_paise", ["e-price_paise-new"])
    repo.save(CatalogEnvelope.model_validate(data))
    result = storage.CatalogRepository(path).read()
    assert result.resolved_value("synthetic-50ml", "price_paise") == 90_000
    assert len(result.observations) == len(catalog()["observations"]) + 1
    repo.save(result)  # Exact replay is safe at the storage boundary.
    assert repo.read() == result


def test_nulls_and_two_variants_do_not_mix(tmp_path: Path) -> None:
    from copy import deepcopy

    path = tmp_path / "variants.db"
    storage.migrate(path)
    data = catalog()
    other = deepcopy(data)
    other["products"][0].update(
        product_id="synthetic-100ml", variant="formulation-a-100ml", pack_size=None
    )
    for item in other["observations"]:
        item["product_id"] = "synthetic-100ml"
        item["evidence_id"] += "-100"
        if item["field_name"] == "variant":
            item["value"] = "formulation-a-100ml"
        elif item["field_name"] in ("pack_size", "price_paise", "rating", "review_count"):
            item["value"] = None
    for item in other["resolutions"]:
        item["product_id"] = "synthetic-100ml"
        item["evidence_ids"] = [eid + "-100" for eid in item["evidence_ids"]]
    for table in ("products", "observations", "resolutions"):
        data[table].extend(other[table])
    value = CatalogEnvelope.model_validate(data)
    repo = storage.CatalogRepository(path)
    repo.save(value)
    assert repo.read() == value
    assert repo.read().resolved_value("synthetic-100ml", "price_paise") is None
    assert repo.read().resolved_value("synthetic-50ml", "rating") is not None


def test_write_failure_rolls_back_inserted_evidence_and_resolution(tmp_path: Path) -> None:
    import pytest
    from test_catalog_contracts import observation

    path = tmp_path / "rollback.db"
    storage.migrate(path)
    repo = storage.CatalogRepository(path)
    original = CatalogEnvelope.model_validate(catalog())
    repo.save(original)
    with storage.connection(path) as con:
        con.execute(
            "CREATE TRIGGER fail_resolution BEFORE INSERT ON resolutions "
            "BEGIN SELECT RAISE(ABORT, 'injected'); END"
        )
    data = catalog()
    data["observations"].append(
        observation("price_paise", 70_000, source="retailer", suffix="-new")
    )
    with pytest.raises(storage.CatalogStorageError, match="Previous data was preserved"):
        repo.save(CatalogEnvelope.model_validate(data))
    assert repo.read() == original


def test_rewriting_or_removing_history_is_rejected(tmp_path: Path) -> None:
    import pytest

    path = tmp_path / "immutable.db"
    storage.migrate(path)
    repo = storage.CatalogRepository(path)
    original = CatalogEnvelope.model_validate(catalog())
    repo.save(original)
    data = catalog()
    next(o for o in data["observations"] if o["field_name"] == "price_paise")["value"] = 1
    with pytest.raises(storage.CatalogStorageError, match="history"):
        repo.save(CatalogEnvelope.model_validate(data))
    with pytest.raises(storage.CatalogStorageError, match="history"):
        repo.save(
            CatalogEnvelope.model_validate(
                {"contract_version": "catalog-v1", **{t: [] for t in storage.TABLES}}
            )
        )
    assert repo.read() == original


def test_sql_constraints_and_foreign_keys(tmp_path: Path) -> None:
    import json
    import sqlite3

    import pytest

    path = tmp_path / "constraints.db"
    storage.migrate(path)
    repo = storage.CatalogRepository(path)
    value = CatalogEnvelope.model_validate(catalog())
    repo.save(value)
    data = catalog()
    invalid = []
    duplicate_variant = dict(data["products"][0], product_id="another-id")
    invalid.extend(
        ("products", item)
        for item in [
            data["products"][0],
            duplicate_variant,
            dict(duplicate_variant, category="invalid"),
        ]
    )
    base = data["observations"][0]
    invalid.extend(
        ("observations", dict(base, evidence_id="bad", **change))
        for change in [
            {"source_id": "missing"},
            {"product_id": "missing"},
            {"field_name": "bad"},
            {"field_name": "review_count", "value": -1},
            {"field_name": "review_count", "value": "12"},
            {"field_name": "sponsorship", "value": "maybe"},
            {"field_name": "rating", "value": {"score": "6", "scale_min": "0", "scale_max": "5"}},
            {"field_name": "rating", "value": {}},
            {"field_name": "skin_type_claims", "value": ["unsupported"]},
            {"field_name": "price_paise", "value": 1, "country": "India", "currency": "USD"},
        ]
    )
    for table, payload in invalid:
        with storage.connection(path) as con:
            assert con.execute("PRAGMA foreign_keys").fetchone()[0] == 1
            con.execute("BEGIN IMMEDIATE")
            with pytest.raises(sqlite3.IntegrityError):
                con.execute(f"INSERT INTO {table}(payload) VALUES (?)", (json.dumps(payload),))
        assert repo.read() == value
    with storage.connection(path) as con:
        with pytest.raises(sqlite3.IntegrityError):
            con.execute(
                "INSERT INTO resolution_evidence VALUES ('synthetic-50ml','rating','e-price_paise')"
            )
        for table in ("products", "sources", "observations"):
            with pytest.raises(sqlite3.IntegrityError):
                con.execute(f"DELETE FROM {table}")


def test_failed_and_successful_forward_migrations(tmp_path: Path, monkeypatch) -> None:
    import pytest

    path = tmp_path / "migration.db"
    storage.migrate(path)
    repo = storage.CatalogRepository(path)
    original = CatalogEnvelope.model_validate(catalog())
    repo.save(original)
    assert storage.migrate(path) is None
    with monkeypatch.context() as patch:
        patch.setattr(storage, "SCHEMA_VERSION", 2)
        patch.setattr(
            storage,
            "MIGRATIONS",
            (*storage.MIGRATIONS, ("CREATE TABLE upgrade_marker(x TEXT)", "INVALID SQL")),
        )
        with pytest.raises(storage.CatalogStorageError, match="migration failed"):
            storage.migrate(path)
    assert repo.read() == original
    with storage.connection(path) as con:
        assert con.execute("PRAGMA user_version").fetchone()[0] == 1
        assert not con.execute(
            "SELECT name FROM sqlite_master WHERE name='upgrade_marker'"
        ).fetchall()
    backups = list((tmp_path / "migration.db.backups").glob("*.db"))
    assert len(backups) == 1
    assert storage.CatalogRepository(backups[0]).read() == original
    with monkeypatch.context() as patch:
        patch.setattr(storage, "SCHEMA_VERSION", 2)
        patch.setattr(
            storage, "MIGRATIONS", (*storage.MIGRATIONS, ("CREATE TABLE upgrade_marker(x TEXT)",))
        )
        assert storage.migrate(path) is not None
        assert storage.migrate(path) is None
        assert repo.read() == original
    restored = tmp_path / "restored.db"
    storage.restore(backups[0], restored)
    assert storage.CatalogRepository(restored).read() == original
    with pytest.raises(storage.CatalogStorageError):
        storage.restore(backups[0], restored)
    assert storage.CatalogRepository(restored).read() == original


def test_unknown_and_newer_schemas_are_untouched(tmp_path: Path) -> None:
    import sqlite3

    import pytest

    for kind in ("foreign", "newer", "unversioned"):
        path = tmp_path / f"{kind}.db"
        if kind == "newer":
            storage.migrate(path)
        with sqlite3.connect(path) as con:
            if kind == "newer":
                con.execute("PRAGMA user_version = 999")
            else:
                con.execute("CREATE TABLE foreign_data(value TEXT)")
        before = path.read_bytes()
        with pytest.raises(storage.CatalogStorageError, match="Unsupported"):
            storage.migrate(path)
        assert path.read_bytes() == before
        with pytest.raises(storage.CatalogStorageError):
            storage.CatalogRepository(path).read()


def test_corruption_and_errors_are_sanitized(tmp_path: Path) -> None:
    import pytest

    path = tmp_path / "private-sentinel.db"
    path.write_text("private-sentinel raw SQL source payload")
    for operation in (
        lambda: storage.migrate(path),
        lambda: storage.CatalogRepository(path).read(),
        lambda: storage.restore(path, tmp_path / "new.db"),
    ):
        with pytest.raises(storage.CatalogStorageError) as caught:
            operation()
        assert "private-sentinel" not in str(caught.value)
        assert caught.value.__suppress_context__


def test_initial_migration_failure_is_retryable(tmp_path: Path, monkeypatch) -> None:
    import pytest

    path = tmp_path / "initial.db"
    with monkeypatch.context() as patch:
        patch.setattr(storage, "MIGRATIONS", ((*storage.MIGRATIONS[0], "INVALID SQL"),))
        with pytest.raises(storage.CatalogStorageError):
            storage.migrate(path)
    with storage.connection(path) as con:
        assert con.execute("PRAGMA user_version").fetchone()[0] == 0
        assert not con.execute("SELECT name FROM sqlite_master").fetchall()
    storage.migrate(path)
    assert not storage.CatalogRepository(path).read().products


def test_backup_failure_prevents_upgrade(tmp_path: Path, monkeypatch) -> None:
    import pytest

    path = tmp_path / "backup.db"
    storage.migrate(path)
    repo = storage.CatalogRepository(path)
    value = CatalogEnvelope.model_validate(catalog())
    repo.save(value)
    # A file occupies the backup directory; failure must precede all migration writes.
    (tmp_path / "backup.db.backups").write_text("synthetic obstruction")
    with monkeypatch.context() as patch:
        patch.setattr(storage, "SCHEMA_VERSION", 2)
        patch.setattr(storage, "MIGRATIONS", (*storage.MIGRATIONS, ("CREATE TABLE bad(x)",)))
        with pytest.raises(storage.CatalogStorageError):
            storage.migrate(path)
    assert repo.read() == value


def test_validated_backup_and_restore(tmp_path: Path) -> None:
    path = tmp_path / "catalog.db"
    storage.migrate(path)
    repo = storage.CatalogRepository(path)
    value = CatalogEnvelope.model_validate(catalog())
    repo.save(value)
    backup = repo.backup()
    assert backup.parent == tmp_path / "catalog.db.backups"
    assert repo.backup() != backup
    restored = tmp_path / "recovered.db"
    storage.restore(backup, restored)
    assert storage.CatalogRepository(restored).read() == value


def test_revalidates_forged_models_and_damaged_links(tmp_path: Path) -> None:
    import pytest

    path = tmp_path / "validated.db"
    storage.migrate(path)
    repo = storage.CatalogRepository(path)
    value = CatalogEnvelope.model_validate(catalog())
    repo.save(value)
    forged = value.model_copy(update={"contract_version": "unsupported"})
    with pytest.raises(storage.CatalogStorageError):
        repo.save(forged)
    assert repo.read() == value
    with storage.connection(path) as con:
        con.execute("DELETE FROM resolution_evidence")
    with pytest.raises(storage.CatalogStorageError, match="evidence links"):
        repo.read()


def test_decimal_rating_does_not_lose_precision_in_sqlite(tmp_path: Path) -> None:
    path = tmp_path / "decimal.db"
    storage.migrate(path)
    data = catalog()
    next(o for o in data["observations"] if o["field_name"] == "rating")["value"] = {
        "score": "1.00000000000000000001",
        "scale_min": "1",
        "scale_max": "1.00000000000000000002",
    }
    value = CatalogEnvelope.model_validate(data)
    repo = storage.CatalogRepository(path)
    repo.save(value)
    assert repo.read() == value


def test_all_optional_explicit_nulls_remain_unknown(tmp_path: Path) -> None:
    data = catalog()
    data["products"][0]["pack_size"] = None
    for item in data["observations"]:
        if item["field_name"] not in ("brand", "name", "category", "variant"):
            item["value"] = None
    value = CatalogEnvelope.model_validate(data)
    path = tmp_path / "nulls.db"
    storage.migrate(path)
    repo = storage.CatalogRepository(path)
    repo.save(value)
    assert repo.read() == value
