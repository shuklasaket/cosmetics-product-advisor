"""US-030 automated catalog journeys using the genuine India demo catalog."""

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from repositories.catalog import migrate
from schemas.catalog import CatalogEnvelope
from services.catalog_import import import_catalog

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
SEED = ROOT / "data/seed/catalog-v1.json"


@pytest.fixture
def genuine_catalog() -> CatalogEnvelope:
    database = Path("database/advisor.db")
    migrate(database)
    assert import_catalog(SEED, database).status == "committed"
    return CatalogEnvelope.model_validate(json.loads(SEED.read_text(encoding="utf-8")))


@pytest.mark.parametrize(
    (
        "category",
        "skin_type",
        "budget",
        "exclusions",
        "texture",
        "finish",
        "product_id",
    ),
    [
        ("Sunscreen", "Oily", "800", "", "", "matte", "minimalist-light-fluid-spf50-50ml"),
        ("Sunscreen", "Sensitive", "400", "fragrance", "gel", "", "foxtale-glow-spf50-50ml"),
        (
            "Sunscreen",
            "Normal",
            "500",
            "oxybenzone",
            "fluid",
            "dewy",
            "aqualogica-glow-dewy-spf50-50g",
        ),
        (
            "Moisturiser",
            "Dry",
            "600",
            "",
            "cream",
            "",
            "reequil-ceramide-ha-moisturiser-100g",
        ),
        (
            "Moisturiser",
            "Combination",
            "350",
            "essential oil",
            "lightweight",
            "",
            "minimalist-vitamin-b5-moisturizer-50g",
        ),
    ],
    ids=[
        "broad-sunscreen-search",
        "budget-sunscreen-with-exclusion",
        "preference-rich-sunscreen-search",
        "dry-skin-moisturiser-search",
        "combination-skin-moisturiser-search",
    ],
)
def test_user_journey_finds_and_inspects_sourced_product(
    genuine_catalog: CatalogEnvelope,
    category: str,
    skin_type: str,
    budget: str,
    exclusions: str,
    texture: str,
    finish: str,
    product_id: str,
) -> None:
    product = next(item for item in genuine_catalog.products if item.product_id == product_id)
    sources = {item.source_id: item for item in genuine_catalog.sources}
    observations = [item for item in genuine_catalog.observations if item.product_id == product_id]

    page = AppTest.from_file(str(APP)).run()
    page.segmented_control(key="search_category").set_value(category)
    page.selectbox(key="search_skin_type").set_value(skin_type)
    page.text_input(key="search_budget").set_value(budget)
    page.text_area(key="search_exclusions").set_value(exclusions)
    page.text_input(key="search_texture").set_value(texture)
    page.text_input(key="search_finish").set_value(finish)
    page.form_submit_button[0].click().run()

    assert not page.exception
    assert page.button(key=f"detail_{product_id}").label == "View details"

    page.button(key=f"detail_{product_id}").click().run()

    visible_text = [element.value for element in page.text]
    expected_attributions = {sources[item.source_id].attribution for item in observations}
    assert not page.exception
    assert page.subheader[-1].value == "Product details"
    assert product.name in visible_text
    assert expected_attributions.intersection(visible_text)
    assert any(link.label == "Open original HTTPS source" for link in page.link_button)
