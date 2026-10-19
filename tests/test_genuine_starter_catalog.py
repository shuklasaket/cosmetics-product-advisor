"""US-019 acceptance checks for the distributable India starter catalog."""

import json
from collections import Counter
from pathlib import Path

from repositories.catalog import CatalogRepository, migrate
from schemas.catalog import CatalogEnvelope
from schemas.requirements import UserRequirements
from services.catalog_import import import_catalog
from services.catalog_search import CatalogSearchService

SEED = Path(__file__).resolve().parents[1] / "data/seed/catalog-v1.json"


def load_seed() -> CatalogEnvelope:
    return CatalogEnvelope.model_validate(json.loads(SEED.read_text(encoding="utf-8")))


def test_genuine_seed_has_required_india_coverage_and_provenance() -> None:
    seed = load_seed()
    assert Counter(product.category for product in seed.products) == {
        "sunscreen": 5,
        "moisturiser": 5,
    }
    assert len({product.product_id for product in seed.products}) == 10
    assert all(source.enabled for source in seed.sources)
    assert all(
        source.permission_reference == "document:us-019-source-policy-v1" for source in seed.sources
    )
    assert all(observation.validation_status == "verified" for observation in seed.observations)
    assert len(seed.resolutions) == len(
        {(item.product_id, item.field_name) for item in seed.resolutions}
    )

    sunscreen = "minimalist-light-fluid-spf50-50ml"
    price = next(
        item
        for item in seed.observations
        if item.product_id == sunscreen and item.field_name == "price_paise"
    )
    ingredients = next(
        item
        for item in seed.observations
        if item.product_id == sunscreen and item.field_name == "ingredient_declaration"
    )
    assert price.source_id.startswith("retailer:")
    assert ingredients.source_id.startswith("maker:")
    assert price.source_id != ingredients.source_id


def test_genuine_seed_import_is_repeatable_and_searchable(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    migrate(database)
    first = import_catalog(SEED, database)
    assert first.status == "committed"
    before = database.read_bytes()
    second = import_catalog(SEED, database)
    assert second.status == "unchanged"
    assert database.read_bytes() == before
    assert len(CatalogRepository(database).read().products) == 10

    service = CatalogSearchService(CatalogRepository(database))
    sunscreen = service.search(
        UserRequirements(category="sunscreen", skin_type="normal", budget_inr="800")
    )
    moisturiser = service.search(
        UserRequirements(category="moisturiser", skin_type="normal", budget_inr="600")
    )
    assert len(sunscreen.catalog.products) == 5
    assert len(moisturiser.catalog.products) == 5
