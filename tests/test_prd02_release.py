"""US-035 strict PRD 02 release-gate checks."""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

from repositories.catalog import CatalogRepository, migrate
from scripts.verify_prd02_release import verify_prd02_release
from services.catalog_import import import_catalog

SEED = Path(__file__).resolve().parents[1] / "data/seed/catalog-v1.json"

RECHECKED_PRODUCTS = {
    "aqualogica-glow-dewy-spf50-50g",
    "foxtale-glow-spf50-50ml",
    "foxtale-hydrating-ceramide-moisturizer-50ml",
    "mamaearth-beetroot-hydraful-moisturizer-50g",
    "mamaearth-cocoa-rich-moisturizing-cream-50g",
    "mamaearth-vitamin-c-daily-glow-spf50-50g",
    "minimalist-light-fluid-spf50-50ml",
    "minimalist-vitamin-b5-moisturizer-50g",
    "reequil-ceramide-ha-moisturiser-100g",
    "reequil-ultra-matte-spf50-50g",
}


def test_rechecked_legacy_facts_keep_history_and_current_selected_evidence(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    migrate(database)
    assert import_catalog(SEED, database).status == "committed"
    catalog = CatalogRepository(database).read()
    selected_ids = {
        evidence_id
        for resolution in catalog.resolutions
        if resolution.status == "selected" and resolution.product_id in RECHECKED_PRODUCTS
        for evidence_id in resolution.evidence_ids
    }
    selected = [item for item in catalog.observations if item.evidence_id in selected_ids]
    cutoff = datetime.fromisoformat("2026-11-26T00:00:00+00:00")

    assert {item.product_id for item in selected} == RECHECKED_PRODUCTS
    assert all(cutoff - item.verified_at <= timedelta(days=7) for item in selected)
    assert all(item.source_reference.startswith("https://") for item in selected)
    assert any(
        item.product_id == "aqualogica-glow-dewy-spf50-50g"
        and item.field_name == "price_paise"
        and item.value == 44900
        for item in selected
    )
    assert any(
        item.product_id == "reequil-ceramide-ha-moisturiser-100g"
        and item.field_name == "price_paise"
        and item.value == 39500
        for item in selected
    )
    assert any(
        item.product_id == "minimalist-light-fluid-spf50-50ml"
        and item.field_name == "ingredient_declaration"
        and item.value.startswith("Water/Aqua, Ethylhexyl Methoxycinnamate")
        for item in selected
    )
    assert any(
        item.product_id == "mamaearth-vitamin-c-daily-glow-spf50-50g"
        and item.field_name == "variant"
        and item.value == "SPF 50 PA++++, 50 g"
        for item in selected
    )
    assert len(
        [item for item in catalog.observations if item.product_id in RECHECKED_PRODUCTS]
    ) > len(selected)


def test_identity_correction_rejects_an_existing_catalog_without_losing_prior_evidence(
    tmp_path: Path,
) -> None:
    current = json.loads(SEED.read_text(encoding="utf-8"))
    previous = json.loads(SEED.read_text(encoding="utf-8"))
    suffix = ":recheck-20261126"
    previous["sources"] = [
        item for item in previous["sources"] if not item["source_id"].endswith(suffix)
    ]
    previous["observations"] = [
        item for item in previous["observations"] if not item["evidence_id"].endswith(suffix)
    ]
    for resolution in previous["resolutions"]:
        resolution["evidence_ids"] = [
            item.removesuffix(suffix) for item in resolution["evidence_ids"]
        ]
    previous_product = next(
        item
        for item in previous["products"]
        if item["product_id"] == "mamaearth-vitamin-c-daily-glow-spf50-50g"
    )
    previous_product["variant"] = "SPF 50 PA+++, 50 g"
    assert len(current["observations"]) - len(previous["observations"]) == 72

    old_batch = tmp_path / "previous-catalog.json"
    old_batch.write_text(json.dumps(previous), encoding="utf-8")
    database = tmp_path / "catalog.db"
    migrate(database)
    assert import_catalog(old_batch, database).status == "committed"

    assert import_catalog(SEED, database).status == "rejected"
    assert import_catalog(SEED, database, update_resolutions=True).status == "rejected"
    retained = CatalogRepository(database).read()
    assert len(retained.observations) == len(previous["observations"])
    assert (
        retained.resolved_value(previous_product["product_id"], "variant") == "SPF 50 PA+++, 50 g"
    )


def test_prd02_gate_fails_closed_until_refresh_history_exists(
    tmp_path: Path,
) -> None:
    database = tmp_path / "catalog.db"
    migrate(database)
    assert import_catalog(SEED, database).status == "committed"

    report = verify_prd02_release(database, today=date(2026, 11, 26))

    assert report.status == "failed"
    assert report.product_count == 25
    assert report.freshness_limits_days == {"price_availability": 7, "other_facts": 30}
    assert "catalog must contain between 20 and 30 exact product variants" not in report.failures
    assert "at least five exact reviewed variant mappings are required" in report.failures
    assert "catalog facts exceed the approved freshness window" not in report.failures


def test_prd02_gate_checks_selected_facts_not_retained_superseded_history(tmp_path: Path) -> None:
    """Old evidence remains inspectable without failing a current-fact freshness check."""
    refreshed = json.loads(SEED.read_text(encoding="utf-8"))
    replacement_ids: dict[str, str] = {}
    for observation in list(refreshed["observations"]):
        replacement_id = f"fresh-{observation['evidence_id']}"
        replacement_ids[observation["evidence_id"]] = replacement_id
        refreshed["observations"].append(
            {
                **observation,
                "evidence_id": replacement_id,
                "retrieved_at": "2026-11-25T12:00:00Z",
                "verified_at": "2026-11-25T12:00:00Z",
                "content_version": "manual-page-review:2026-11-25",
                "snapshot_id": f"fresh-{observation['snapshot_id']}",
            }
        )
    for resolution in refreshed["resolutions"]:
        resolution["evidence_ids"] = [replacement_ids[item] for item in resolution["evidence_ids"]]

    batch = tmp_path / "fresh-selected-catalog.json"
    batch.write_text(json.dumps(refreshed), encoding="utf-8")
    database = tmp_path / "catalog.db"
    migrate(database)
    assert import_catalog(batch, database).status == "committed"

    report = verify_prd02_release(database, today=date(2026, 11, 25))

    assert "catalog facts exceed the approved freshness window" not in report.failures
