"""US-020 release checks using the genuine India demo catalog."""

import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from repositories.catalog import CatalogRepository, migrate, restore
from scripts.verify_catalog_release import verify_catalog_release
from services.catalog_import import import_catalog

SEED = Path(__file__).resolve().parents[1] / "data/seed/catalog-v1.json"
APP = Path(__file__).resolve().parents[1] / "app.py"


def test_release_verifier_checks_required_searches_and_mixed_provenance(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    migrate(database)
    assert import_catalog(SEED, database).status == "committed"

    report = verify_catalog_release(database)

    assert report.status == "passed"
    assert report.product_count == 10
    assert set(report.sunscreen_ids) == {
        "aqualogica-glow-dewy-spf50-50g",
        "foxtale-glow-spf50-50ml",
        "mamaearth-vitamin-c-daily-glow-spf50-50g",
        "minimalist-light-fluid-spf50-50ml",
        "reequil-ultra-matte-spf50-50g",
    }
    assert len(report.moisturiser_ids) == 5
    assert report.provenance_product_id == "minimalist-light-fluid-spf50-50ml"
    assert report.price_source_id.startswith("retailer:")
    assert report.ingredients_source_id.startswith("maker:")
    assert report.price_source_id != report.ingredients_source_id
    assert report.price_verified_at
    assert report.ingredients_verified_at


def test_release_verifier_passes_after_validated_backup_restore(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    migrate(database)
    assert import_catalog(SEED, database).status == "committed"
    backup = CatalogRepository(database).backup()
    recovered = tmp_path / "recovered.db"

    restore(backup, recovered)

    assert verify_catalog_release(recovered).status == "passed"


def test_genuine_catalog_is_discoverable_with_separate_price_and_ingredient_evidence() -> None:
    database = Path("database/advisor.db")
    migrate(database)
    assert import_catalog(SEED, database).status == "committed"
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    observations = {(item["product_id"], item["field_name"]): item for item in seed["observations"]}
    sources = {item["source_id"]: item for item in seed["sources"]}
    product_id = "minimalist-light-fluid-spf50-50ml"
    price = observations[(product_id, "price_paise")]
    ingredients = observations[(product_id, "ingredient_declaration")]

    page = AppTest.from_file(str(APP)).run()
    page.text_input(key="search_budget").set_value("800")
    page.form_submit_button[0].click().run()

    assert not page.exception
    detail_buttons = [button for button in page.button if button.key.startswith("detail_")]
    assert len(detail_buttons) == 5
    page.button(key=f"detail_{product_id}").click().run()

    visible_text = [item.value for item in page.text]
    assert sources[price["source_id"]]["attribution"] in visible_text
    assert sources[ingredients["source_id"]]["attribution"] in visible_text
    assert price["verified_at"] in visible_text
    assert ingredients["verified_at"] in visible_text
    assert price["source_id"] != ingredients["source_id"]
    assert not page.exception
