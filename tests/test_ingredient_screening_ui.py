"""US-057 product-detail screening panel checks."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from repositories.catalog import migrate
from services.catalog_import import import_catalog
from ui.search_form import clear_search_state

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
SEED = ROOT / "data/seed/catalog-v1.json"


def test_detail_shows_limited_screening_and_recomputes_session_exclusions() -> None:
    migrate(Path("database/advisor.db"))
    assert import_catalog(SEED, Path("database/advisor.db")).status == "committed"
    page = AppTest.from_file(str(APP)).run()
    page.segmented_control(key="search_category").set_value("Moisturiser")
    page.text_input(key="search_budget").set_value("2000")
    page.form_submit_button[0].click().run()
    page.button(key="detail_cerave-oil-control-gel-cream-52ml").click().run()

    assert not page.exception
    assert any("Ingredient screening" in item.value for item in page.markdown)
    assert "limited rule set" in " ".join(item.value for item in page.caption).lower()

    page.text_area(key="screening_avoid_list").set_value("Glycerin").run()

    assert not page.exception
    assert any("personal exclusion match: glycerin" in item.value.lower() for item in page.warning)
    assert any("excluded" in item.value.lower() for item in page.text)


def test_screening_clear_removes_session_only_avoid_list() -> None:
    state: dict[str, object] = {
        "screening_avoid_list": "synthetic-private-ingredient",
        "ingredient_rule_manifest_store": object(),
    }

    clear_search_state(state)

    assert "screening_avoid_list" not in state
    assert "ingredient_rule_manifest_store" not in state
