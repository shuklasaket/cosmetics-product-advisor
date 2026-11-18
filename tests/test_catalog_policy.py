"""US-038: deterministic conflict, freshness, and qualification policy."""

from datetime import UTC, datetime, timedelta

from test_catalog_contracts import catalog, observation, source

from schemas.catalog import CatalogEnvelope
from services.catalog_policy import evaluate_catalog

NOW = datetime(2026, 10, 28, 12, tzinfo=UTC)


def envelope_with_conflicts() -> CatalogEnvelope:
    data = catalog()
    for item in data["sources"]:
        item["source_type"] = "manufacturer" if item["source_id"] == "maker" else "retailer"
    data["sources"].append(source("open-beauty-facts") | {"source_type": "dataset"})
    manufacturer_price = observation("price_paise", 90_000, source="maker", suffix="-maker")
    retailer_ingredients = observation(
        "ingredient_declaration", "Other ingredients", source="retailer", suffix="-retailer"
    )
    obf_ingredients = observation(
        "ingredient_declaration", "OBF ingredients", source="open-beauty-facts", suffix="-obf"
    )
    data["observations"].extend((manufacturer_price, retailer_ingredients, obf_ingredients))
    for field, evidence_ids in {
        "price_paise": ["e-price_paise", "e-price_paise-maker"],
        "ingredient_declaration": [
            "e-ingredient_declaration",
            "e-ingredient_declaration-retailer",
            "e-ingredient_declaration-obf",
        ],
    }.items():
        resolution = next(item for item in data["resolutions"] if item["field_name"] == field)
        resolution["status"] = "unresolved"
        resolution["evidence_ids"] = evidence_ids
    return CatalogEnvelope.model_validate(data)


def test_policy_prefers_explicit_sources_and_retains_conflicts() -> None:
    value = envelope_with_conflicts()

    result = evaluate_catalog(value, now=NOW)

    price = result.fact("synthetic-50ml", "price_paise")
    ingredients = result.fact("synthetic-50ml", "ingredient_declaration")
    assert price.selected_evidence_id == "e-price_paise"
    assert ingredients.selected_evidence_id == "e-ingredient_declaration"
    assert price.conflicting_evidence_ids == ("e-price_paise-maker",)
    assert ingredients.conflicting_evidence_ids == (
        "e-ingredient_declaration-retailer",
        "e-ingredient_declaration-obf",
    )
    assert value.resolved_value("synthetic-50ml", "price_paise") is None


def test_policy_withholds_unresolved_same_precedence_and_stale_critical_facts() -> None:
    data = catalog()
    stale_at = (NOW - timedelta(days=8)).isoformat().replace("+00:00", "Z")
    price = next(item for item in data["observations"] if item["field_name"] == "price_paise")
    price["retrieved_at"] = stale_at
    price["verified_at"] = stale_at
    availability = next(
        item for item in data["observations"] if item["field_name"] == "availability"
    )
    availability["retrieved_at"] = NOW.isoformat().replace("+00:00", "Z")
    availability["verified_at"] = availability["retrieved_at"]
    duplicate = observation("ingredient_declaration", "Other ingredients", suffix="-other")
    data["observations"].append(duplicate)
    resolution = next(
        item for item in data["resolutions"] if item["field_name"] == "ingredient_declaration"
    )
    resolution["status"] = "unresolved"
    resolution["evidence_ids"] = ["e-ingredient_declaration", "e-ingredient_declaration-other"]

    result = evaluate_catalog(CatalogEnvelope.model_validate(data), now=NOW)

    assert result.fact("synthetic-50ml", "price_paise").freshness == "stale"
    qualification = result.qualification("synthetic-50ml")
    assert not qualification.qualified
    assert qualification.reason_codes == ("stale_price", "unresolved_ingredient")


def test_policy_withholds_missing_critical_facts() -> None:
    data = catalog()
    data["observations"] = [
        item for item in data["observations"] if item["field_name"] != "ingredient_declaration"
    ]
    data["resolutions"] = [
        item for item in data["resolutions"] if item["field_name"] != "ingredient_declaration"
    ]

    result = evaluate_catalog(
        CatalogEnvelope.model_validate(data), now=datetime(2026, 10, 19, 12, tzinfo=UTC)
    )

    assert result.qualification("synthetic-50ml").reason_codes == ("unresolved_ingredient",)


def test_policy_applies_30_day_window_to_non_offer_facts_at_boundary() -> None:
    data = catalog()
    ingredient = next(
        item for item in data["observations"] if item["field_name"] == "ingredient_declaration"
    )
    ingredient["retrieved_at"] = (NOW - timedelta(days=30)).isoformat().replace("+00:00", "Z")
    ingredient["verified_at"] = ingredient["retrieved_at"]

    result = evaluate_catalog(CatalogEnvelope.model_validate(data), now=NOW)

    assert result.fact("synthetic-50ml", "ingredient_declaration").freshness == "fresh"
