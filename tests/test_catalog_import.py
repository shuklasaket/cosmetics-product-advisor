"""US-015: synthetic local files and temporary real SQLite, never genuine seed data."""

import json
from pathlib import Path

import pytest
from test_catalog_contracts import catalog

from repositories.catalog import CatalogRepository, migrate
from schemas.catalog import CatalogEnvelope
from services import catalog_import as importer


def write_batch(tmp_path: Path, data: dict | None = None) -> Path:
    path = tmp_path / "batch.json"
    path.write_text(json.dumps(catalog() if data is None else data), encoding="utf-8")
    return path


def test_import_preserves_field_provenance_and_unknowns(tmp_path: Path) -> None:
    data = catalog()
    data["observations"] = [o for o in data["observations"] if o["field_name"] != "sponsorship"]
    data["resolutions"] = [r for r in data["resolutions"] if r["field_name"] != "sponsorship"]
    batch = write_batch(tmp_path, data)
    database = tmp_path / "catalog.db"
    migrate(database)
    report = importer.import_catalog(batch, database)
    assert report.committed
    assert report.accepted == sum(
        len(data[t]) for t in ("products", "sources", "observations", "resolutions")
    )
    assert report.rejected == 0
    assert not report.issues
    stored = CatalogRepository(database).read()
    assert stored == CatalogEnvelope.model_validate(data)
    by_field = {o.field_name: o for o in stored.observations}
    assert by_field["price_paise"].source_id == "retailer"
    assert by_field["ingredient_declaration"].source_id == "maker"
    assert stored.resolved_value("synthetic-50ml", "sponsorship") is None


def test_invalid_rows_reject_whole_batch_with_safe_row_identifiers(tmp_path: Path) -> None:
    data = catalog()
    del data["products"][0]["name"]
    del data["sources"][0]["reuse_conditions"]
    data["observations"][0]["source_id"] = "unknown-source"
    next(o for o in data["observations"] if o["field_name"] == "price_paise")["value"] = -1
    database = tmp_path / "catalog.db"
    migrate(database)
    before = CatalogRepository(database).read()
    report = importer.import_catalog(write_batch(tmp_path, data), database)
    assert report.status == "rejected"
    assert report.accepted == 0
    assert report.rejected == sum(
        len(data[t]) for t in ("products", "sources", "observations", "resolutions")
    )
    assert not report.committed
    messages = {issue.row: issue.message for issue in report.issues}
    assert "name" in messages["products:1"]
    assert "reuse_conditions" in messages["sources:1"]
    assert "source" in messages["observations:1"]
    assert len(messages) == report.rejected
    assert CatalogRepository(database).read() == before
    rendered = str(report)
    assert "unknown-source" not in rendered
    assert "Synthetic Screen" not in rendered


def test_reimport_is_reported_unchanged_without_writing(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    migrate(database)
    batch = write_batch(tmp_path)
    assert importer.import_catalog(batch, database).committed
    before = database.read_bytes()
    report = importer.import_catalog(batch, database)
    assert report.status == "unchanged"
    assert not report.committed
    assert report.accepted == report.unchanged > 0
    assert report.updated_resolutions == 0
    assert database.read_bytes() == before


def test_resolution_update_requires_explicit_flag_and_retains_history(tmp_path: Path) -> None:
    from test_catalog_contracts import observation, select

    database = tmp_path / "catalog.db"
    migrate(database)
    batch = write_batch(tmp_path)
    importer.import_catalog(batch, database)
    original = CatalogRepository(database).read()
    data = catalog()
    data["observations"].append(
        observation("price_paise", 90_000, source="retailer", suffix="-new")
    )
    data["resolutions"] = [r for r in data["resolutions"] if r["field_name"] != "price_paise"]
    data["resolutions"].append(
        select("price_paise", ["e-price_paise", "e-price_paise-new"], "unresolved")
    )
    batch = write_batch(tmp_path, data)
    report = importer.import_catalog(batch, database)
    assert report.status == "rejected"
    assert "--update-resolutions" in str(report)
    assert CatalogRepository(database).read() == original
    report = importer.import_catalog(batch, database, update_resolutions=True)
    assert report.committed
    assert report.updated_resolutions == 1
    assert report.unresolved == 1
    stored = CatalogRepository(database).read()
    assert len(stored.observations) == len(original.observations) + 1
    assert stored.resolved_value("synthetic-50ml", "price_paise") is None
    # Default replay of the old batch must not silently restore an obsolete selection.
    report = importer.import_catalog(write_batch(tmp_path), database)
    assert report.status == "rejected"
    assert CatalogRepository(database).read() == stored


@pytest.mark.parametrize(
    "contents",
    [
        '{"private-sentinel":',
        '{"contract_version":"catalog-v1","contract_version":"catalog-v1"}',
        "NaN",
        "\ufeff{}",
    ],
)
def test_malformed_json_is_sanitized_and_preserves_database(tmp_path: Path, contents: str) -> None:
    database = tmp_path / "catalog.db"
    migrate(database)
    CatalogRepository(database).save(CatalogEnvelope.model_validate(catalog()))
    before = database.read_bytes()
    batch = tmp_path / "private-sentinel.json"
    batch.write_text(contents, encoding="utf-8")
    report = importer.import_catalog(batch, database)
    assert report.status == "failed"
    assert not report.committed
    assert not report.rows_known
    assert "private-sentinel" not in str(report)
    assert database.read_bytes() == before


def test_missing_input_and_database_fail_without_creating_storage(tmp_path: Path) -> None:
    database = tmp_path / "missing.db"
    report = importer.import_catalog(tmp_path / "private-sentinel.json", database)
    assert report.status == "failed"
    assert not database.exists()
    report = importer.import_catalog(write_batch(tmp_path), database)
    assert report.status == "failed"
    assert not report.committed
    assert report.rejected > 0
    assert not database.exists()


def test_injected_write_failure_keeps_last_valid_catalog(tmp_path: Path) -> None:
    from test_catalog_contracts import observation

    database = tmp_path / "catalog.db"
    migrate(database)
    importer.import_catalog(write_batch(tmp_path), database)
    original = CatalogRepository(database).read()
    from repositories.catalog import connection

    with connection(database) as con:
        con.execute(
            "CREATE TRIGGER fail_resolution BEFORE INSERT ON resolutions "
            "BEGIN SELECT RAISE(ABORT, 'private-sentinel'); END"
        )
    data = catalog()
    data["observations"].append(observation("price_paise", 1, source="retailer", suffix="-new"))
    report = importer.import_catalog(write_batch(tmp_path, data), database)
    assert report.status == "failed"
    assert not report.committed
    assert "private-sentinel" not in str(report)
    assert CatalogRepository(database).read() == original


def test_concurrent_import_does_not_overwrite_newer_resolution(tmp_path: Path, monkeypatch) -> None:
    from test_catalog_contracts import select

    database = tmp_path / "catalog.db"
    migrate(database)
    importer.import_catalog(write_batch(tmp_path), database)
    data = catalog()
    next(r for r in data["resolutions"] if r["field_name"] == "review_count")["status"] = (
        "unresolved"
    )
    newer = CatalogEnvelope.model_validate(data)
    save = CatalogRepository.save

    def competing_save(self, value, *, expected=None):
        save(self, newer)
        save(self, value, expected=expected)

    monkeypatch.setattr(CatalogRepository, "save", competing_save)
    incoming = catalog()
    incoming["resolutions"] = [
        r for r in incoming["resolutions"] if r["field_name"] != "price_paise"
    ]
    incoming["resolutions"].append(select("price_paise", status="unresolved"))
    report = importer.import_catalog(
        write_batch(tmp_path, incoming), database, update_resolutions=True
    )
    assert report.status == "failed"
    assert not report.committed
    assert CatalogRepository(database).read() == newer


def test_cli_prints_only_sanitized_json_and_exit_status(tmp_path: Path, capsys) -> None:
    from scripts import import_catalog as command

    database = tmp_path / "catalog.db"
    migrate(database)
    batch = write_batch(tmp_path)
    assert command.main([str(batch), "--database", str(database)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["committed"]
    assert summary["status"] == "committed"
    assert "Synthetic" not in json.dumps(summary)
    assert command.main([str(batch), "--database", str(database)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "unchanged"
    batch.write_text("private-sentinel", encoding="utf-8")
    assert command.main([str(batch), "--database", str(database)]) == 1
    output = capsys.readouterr()
    assert "private-sentinel" not in output.out + output.err
    assert json.loads(output.out)["committed"] is False


@pytest.mark.parametrize("table", ["products", "sources", "observations", "resolutions"])
def test_duplicate_batch_rows_are_rejected_even_when_identical(tmp_path: Path, table: str) -> None:
    data = catalog()
    data[table].append(dict(data[table][0]))
    database = tmp_path / "catalog.db"
    migrate(database)
    report = importer.import_catalog(write_batch(tmp_path, data), database)
    assert report.status == "rejected"
    assert "duplicate" in str(report).lower()
    assert not CatalogRepository(database).read().products
    assert report.rejected == sum(len(data[t]) for t in importer.MODELS)


@pytest.mark.parametrize(
    "table,field",
    [("products", "name"), ("sources", "attribution"), ("observations", "content_version")],
)
def test_import_cannot_rewrite_immutable_ids(tmp_path: Path, table: str, field: str) -> None:
    database = tmp_path / "catalog.db"
    migrate(database)
    importer.import_catalog(write_batch(tmp_path), database)
    original = CatalogRepository(database).read()
    data = catalog()
    data[table][0][field] = "changed"
    # Keep identity evidence consistent so this case reaches the cross-import policy.
    if table == "products":
        next(o for o in data["observations"] if o["field_name"] == "name")["value"] = "changed"
    report = importer.import_catalog(write_batch(tmp_path, data), database, update_resolutions=True)
    assert report.status == "rejected"
    assert "immutable" in str(report)
    assert CatalogRepository(database).read() == original


def test_subset_batch_appends_without_removing_existing_products(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    migrate(database)
    importer.import_catalog(write_batch(tmp_path), database)
    original = CatalogRepository(database).read()
    data = catalog()
    data["products"][0].update(
        product_id="synthetic-100ml", variant="formulation-a-100ml", pack_size="100 ml"
    )
    for item in data["observations"]:
        item["product_id"] = "synthetic-100ml"
        item["evidence_id"] += "-100"
        if item["field_name"] == "variant":
            item["value"] = "formulation-a-100ml"
        elif item["field_name"] == "pack_size":
            item["value"] = "100 ml"
    for item in data["resolutions"]:
        item["product_id"] = "synthetic-100ml"
        item["evidence_ids"] = [eid + "-100" for eid in item["evidence_ids"]]
    report = importer.import_catalog(write_batch(tmp_path, data), database)
    assert report.committed
    assert report.unchanged == 2  # Reuse both registered sources.
    stored = CatalogRepository(database).read()
    assert len(stored.products) == 2
    assert all(o in stored.observations for o in original.observations)


def test_second_id_for_existing_variant_is_rejected_after_merge(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    migrate(database)
    importer.import_catalog(write_batch(tmp_path), database)
    original = CatalogRepository(database).read()
    data = catalog()
    data["products"][0]["product_id"] = "second-id"
    for item in data["observations"]:
        item["product_id"] = "second-id"
        item["evidence_id"] += "-second"
    for item in data["resolutions"]:
        item["product_id"] = "second-id"
        item["evidence_ids"] = [eid + "-second" for eid in item["evidence_ids"]]
    report = importer.import_catalog(write_batch(tmp_path, data), database)
    assert report.status == "rejected"
    assert "variant" in str(report)
    assert CatalogRepository(database).read() == original


@pytest.mark.parametrize(
    "mutation", ["disabled", "permission", "unknown", "unverified", "snapshot"]
)
def test_source_permission_and_evidence_links_are_required(tmp_path: Path, mutation: str) -> None:
    data = catalog()
    if mutation == "disabled":
        data["sources"][0]["enabled"] = False
    elif mutation == "permission":
        data["sources"][0]["permission_reference"] = ""
    elif mutation == "unknown":
        data["observations"][0]["source_id"] = "missing"
    elif mutation == "unverified":
        data["observations"][0]["validation_status"] = "unverified"
    else:
        next(o for o in data["observations"] if o["field_name"] == "rating")["snapshot_id"] = (
            "incompatible"
        )
    database = tmp_path / "catalog.db"
    migrate(database)
    report = importer.import_catalog(write_batch(tmp_path, data), database)
    assert report.status == "rejected"
    assert not CatalogRepository(database).read().observations


def test_limits_encoding_shapes_and_unknown_fields_do_not_leak(tmp_path: Path, monkeypatch) -> None:
    database = tmp_path / "absent.db"
    batch = tmp_path / "private-sentinel.json"
    monkeypatch.setattr(importer, "MAX_INPUT_BYTES", 32)
    batch.write_bytes(b" " * 33)
    assert not importer.import_catalog(batch, database).rows_known
    batch.write_bytes(b"\xff")
    assert importer.import_catalog(batch, database).status == "failed"
    for payload in [[], None, {}, {"private-sentinel": 1}, {"contract_version": "catalog-v2"}]:
        batch.write_text(json.dumps(payload), encoding="utf-8")
        report = importer.import_catalog(batch, database)
        assert not report.committed
        assert "private-sentinel" not in str(report)
    assert not database.exists()


def test_cli_configuration_and_argument_failures_are_sanitized(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from scripts import import_catalog as command

    assert command.main(["private-sentinel", "--private-sentinel"]) == 1
    assert "private-sentinel" not in capsys.readouterr().out
    monkeypatch.setenv("ADVISOR_DATABASE_PATH", "")
    assert command.main(["private-sentinel"]) == 1
    output = capsys.readouterr()
    assert "private-sentinel" not in output.out + output.err
    assert json.loads(output.out)["issues"][0]["row"] == "configuration"


def test_cli_uses_settings_database_path(tmp_path: Path, monkeypatch, capsys) -> None:
    from scripts import import_catalog as command

    database = tmp_path / "configured.db"
    migrate(database)
    monkeypatch.setenv("ADVISOR_DATABASE_PATH", str(database))
    assert command.main([str(write_batch(tmp_path))]) == 0
    assert json.loads(capsys.readouterr().out)["committed"]
    assert len(CatalogRepository(database).read().products) == 1


def test_json_numeric_ratings_keep_exact_decimal_text(tmp_path: Path) -> None:
    from decimal import Decimal

    data = catalog()
    next(o for o in data["observations"] if o["field_name"] == "rating")["value"] = {
        "score": "EXACT_NUMBER",
        "scale_min": "0",
        "scale_max": "5",
    }
    batch = write_batch(tmp_path, data)
    batch.write_text(
        batch.read_text().replace('"EXACT_NUMBER"', "4.123456789012345678901"), encoding="utf-8"
    )
    database = tmp_path / "catalog.db"
    migrate(database)
    assert importer.import_catalog(batch, database).committed
    rating = CatalogRepository(database).read().resolved_value("synthetic-50ml", "rating")
    assert rating.score == Decimal("4.123456789012345678901")


def test_module_command_from_separate_process(tmp_path: Path) -> None:
    import os
    import subprocess
    import sys

    database = tmp_path / "catalog.db"
    migrate(database)
    batch = write_batch(tmp_path)
    environment = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
    result = subprocess.run(
        [sys.executable, "-m", "scripts.import_catalog", str(batch), "--database", str(database)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["committed"]
    assert not result.stderr


def test_extreme_json_number_is_a_sanitized_failure(tmp_path: Path) -> None:
    batch = tmp_path / "private-sentinel.json"
    batch.write_text("1e999999999999999999999", encoding="utf-8")
    report = importer.import_catalog(batch, tmp_path / "missing.db")
    assert report.status == "failed"
    assert not report.rows_known
    assert "private-sentinel" not in str(report)


def test_cli_unreadable_configuration_is_sanitized(tmp_path: Path, monkeypatch, capsys) -> None:
    from scripts import import_catalog as command

    def unreadable_settings():
        raise OSError("private-sentinel")

    monkeypatch.setattr(command, "Settings", unreadable_settings)
    assert command.main([str(write_batch(tmp_path))]) == 1
    output = capsys.readouterr()
    assert "private-sentinel" not in output.out + output.err
    assert json.loads(output.out)["issues"][0]["row"] == "configuration"
