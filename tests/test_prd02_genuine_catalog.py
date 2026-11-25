"""US-035 acceptance checks for the expanded genuine India catalog."""

import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

from schemas.catalog import CatalogEnvelope

SEED = Path(__file__).resolve().parents[1] / "data/seed/catalog-v1.json"

EXPECTED_ADDITIONS = {
    "minimalist-multi-vitamin-spf50-50g",
    "foxtale-dewy-finish-spf50-50ml",
    "reequil-oxybenzone-free-spf50-50g",
    "aqualogica-hydrate-dewy-spf50-50g",
    "aqualogica-illuminate-dewy-spf50-50g",
    "minimalist-marula-oil-moisturizer-50g",
    "reequil-oil-free-moisturiser-50g",
    "foxtale-oil-balancing-moisturizer-50ml",
    "foxtale-brightening-moisturizer-50ml",
    "aqualogica-glow-jello-moisturizer-50g",
}

EXPECTED_REVIEWED_MAPPINGS = {
    "la-shield-fisico-matte-spf50-50g",
    "cerave-oil-control-gel-cream-52ml",
    "cerave-moisturising-lotion-236ml",
    "bioderma-atoderm-cream-ultra-200ml",
    "cerave-facial-moisturising-am-spf30-52ml",
}


def load_seed() -> CatalogEnvelope:
    return CatalogEnvelope.model_validate(json.loads(SEED.read_text(encoding="utf-8")))


def test_prd02_seed_has_twenty_five_exact_india_variants() -> None:
    seed = load_seed()

    assert Counter(product.category for product in seed.products) == {
        "sunscreen": 12,
        "moisturiser": 13,
    }
    assert {product.product_id for product in seed.products} >= EXPECTED_ADDITIONS
    assert all(product.pack_size for product in seed.products)


def test_prd02_additions_use_reviewed_official_storefront_evidence() -> None:
    seed = load_seed()
    new_sources = [
        source
        for source in seed.sources
        if source.source_id.removeprefix("maker:").removeprefix("retailer:") in EXPECTED_ADDITIONS
    ]

    assert len(new_sources) == len(EXPECTED_ADDITIONS) * 2
    assert all(source.enabled for source in new_sources)
    assert all(
        source.permission_reference == "document:us-019-source-policy-v1" for source in new_sources
    )
    assert all(
        urlsplit(source.source_reference).hostname != "www.bigbasket.com" for source in new_sources
    )
    assert {source.source_type for source in new_sources} == {"manufacturer", "retailer"}

    fields = {
        product_id: {
            observation.field_name
            for observation in seed.observations
            if observation.product_id == product_id
        }
        for product_id in EXPECTED_ADDITIONS
    }
    assert all(
        {"brand", "name", "category", "variant", "pack_size", "availability", "price_paise"}
        <= product_fields
        for product_fields in fields.values()
    )
    assert all(
        observation.validation_status == "verified"
        for observation in seed.observations
        if observation.product_id in EXPECTED_ADDITIONS
    )


def test_prd02_reviewed_mappings_select_complete_obf_formulations() -> None:
    seed = load_seed()
    selected_ingredients = {
        resolution.product_id: resolution.evidence_ids
        for resolution in seed.resolutions
        if resolution.field_name == "ingredient_declaration" and resolution.status == "selected"
    }
    mapped_observations = {
        observation.evidence_id: observation
        for observation in seed.observations
        if observation.product_id in EXPECTED_REVIEWED_MAPPINGS
        and observation.field_name == "ingredient_declaration"
    }

    assert set(selected_ingredients) >= EXPECTED_REVIEWED_MAPPINGS
    assert all(
        mapped_observations[evidence_id].source_id == "open-beauty-facts"
        and mapped_observations[evidence_id].validation_status == "verified"
        and mapped_observations[evidence_id].value
        for product_id in EXPECTED_REVIEWED_MAPPINGS
        for evidence_id in selected_ingredients[product_id]
    )
