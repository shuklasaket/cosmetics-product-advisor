"""Synthetic evidence for US-013 AC-3/AC-4, never a genuine seed catalog."""

from copy import deepcopy
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from schemas.catalog import CatalogEnvelope

STAMP = "2026-10-19T10:00:00Z"


def observation(field: str, value: object, *, source: str = "maker", suffix: str = "") -> dict:
    return {
        "evidence_id": f"e-{field}{suffix}",
        "product_id": "synthetic-50ml",
        "source_id": source,
        "field_name": field,
        "value": value,
        "source_reference": "https://example.test/facts",
        "retrieved_at": STAMP,
        "verified_at": STAMP,
        "content_version": "sha256:synthetic",
        "snapshot_id": "snapshot-1",
        "validation_status": "verified",
        **({"country": "India", "currency": "INR"} if field == "price_paise" else {}),
    }


def select(field: str, ids: list[str] | None = None, status: str = "selected") -> dict:
    return {
        "product_id": "synthetic-50ml",
        "field_name": field,
        "status": status,
        "evidence_ids": ids or [f"e-{field}"],
        "policy_version": "explicit-selection-v1",
    }


def source(source_id: str) -> dict:
    return {
        "source_id": source_id,
        "source_type": "document",
        "source_reference": "document:synthetic-permission-record",
        "access_conditions": "Synthetic test only",
        "reuse_conditions": "Synthetic test only",
        "permission_reference": "document:synthetic-terms",
        "attribution": "Synthetic fixture",
        "last_checked": STAMP,
        "enabled": True,
    }


def catalog() -> dict:
    identity = {
        "brand": "Synthetic Brand",
        "name": "Synthetic Screen",
        "category": "sunscreen",
        "variant": "formulation-a-50ml",
        "pack_size": "50 ml",
    }
    facts = {
        **identity,
        "availability": ["India"],
        "price_paise": 80_000,
        "skin_type_claims": ["oily"],
        "rating": {"score": "4.2", "scale_min": "0", "scale_max": "5"},
        "review_count": 12,
        "ingredient_declaration": "Synthetic A, B",
        "ingredient_completeness": "complete",
        "sponsorship": "unknown",
    }
    observations = [
        observation(
            k, v, source="retailer" if k in ("price_paise", "rating", "review_count") else "maker"
        )
        for k, v in facts.items()
    ]
    return {
        "contract_version": "catalog-v1",
        "sources": [source("maker"), source("retailer")],
        "products": [{"product_id": "synthetic-50ml", **identity}],
        "observations": observations,
        "resolutions": [select(k) for k in facts],
    }


def test_round_trip_preserves_field_sources_and_typed_values() -> None:
    value = CatalogEnvelope.model_validate(catalog())
    assert CatalogEnvelope.model_validate_json(value.model_dump_json()) == value
    by_field = {o.field_name: o for o in value.observations}
    assert by_field["price_paise"].value == 80_000
    assert by_field["price_paise"].source_id == "retailer"
    assert by_field["ingredient_declaration"].source_id == "maker"
    assert by_field["rating"].value.score == Decimal("4.2")
    assert all(o.verified_at.tzinfo == UTC for o in value.observations)


def test_missing_optional_facts_remain_unknown_without_synthetic_defaults() -> None:
    data = catalog()
    required = {"brand", "name", "category", "variant"}
    data["products"][0]["pack_size"] = None
    data["observations"] = [o for o in data["observations"] if o["field_name"] in required]
    data["resolutions"] = [r for r in data["resolutions"] if r["field_name"] in required]
    value = CatalogEnvelope.model_validate(data)
    assert value.products[0].pack_size is None
    assert len(value.resolutions) == 4


@pytest.mark.parametrize(
    "field",
    [
        "price_paise",
        "availability",
        "skin_type_claims",
        "rating",
        "review_count",
        "ingredient_declaration",
        "ingredient_completeness",
        "sponsorship",
        "pack_size",
    ],
)
def test_explicit_null_observations_are_unknown(field: str) -> None:
    data = catalog()
    next(o for o in data["observations"] if o["field_name"] == field)["value"] = None
    if field == "pack_size":
        data["products"][0]["pack_size"] = None
    CatalogEnvelope.model_validate(data)


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("price_paise", True),
        ("price_paise", "80000"),
        ("price_paise", 80000.1),
        ("price_paise", -1),
        ("review_count", -1),
        ("review_count", True),
        ("availability", "India"),
        ("availability", [""]),
        ("skin_type_claims", ["other"]),
        ("ingredient_declaration", ""),
        ("ingredient_completeness", "safe"),
        ("sponsorship", False),
        ("sponsorship", "sponsored"),
        ("rating", {"score": "4.2"}),
        ("rating", {"score": "6", "scale_min": "0", "scale_max": "5"}),
        ("rating", {"score": "NaN", "scale_min": "0", "scale_max": "5"}),
        ("rating", {"score": True, "scale_min": 0, "scale_max": 5}),
        ("rating", {"score": 0, "scale_min": 5, "scale_max": 5}),
    ],
)
def test_invalid_fact_types_units_and_ranges_fail(field: str, bad: object) -> None:
    data = catalog()
    next(o for o in data["observations"] if o["field_name"] == field)["value"] = bad
    with pytest.raises(ValidationError):
        CatalogEnvelope.model_validate(data)


@pytest.mark.parametrize("part", ["products", "sources", "observations", "resolutions"])
def test_duplicate_ids_or_resolution_keys_are_rejected(part: str) -> None:
    data = catalog()
    data[part].append(deepcopy(data[part][0]))
    with pytest.raises(ValidationError):
        CatalogEnvelope.model_validate(data)


@pytest.mark.parametrize("missing", ["brand", "name", "category", "variant"])
def test_missing_identity_or_identity_provenance_is_rejected(missing: str) -> None:
    data = catalog()
    data["products"][0].pop(missing)
    with pytest.raises(ValidationError):
        CatalogEnvelope.model_validate(data)
    data = catalog()
    data["resolutions"] = [r for r in data["resolutions"] if r["field_name"] != missing]
    with pytest.raises(ValidationError):
        CatalogEnvelope.model_validate(data)


@pytest.mark.parametrize(
    "field",
    [
        "source_id",
        "source_reference",
        "retrieved_at",
        "verified_at",
        "content_version",
        "snapshot_id",
    ],
)
def test_missing_observation_provenance_is_rejected(field: str) -> None:
    data = catalog()
    data["observations"][0].pop(field)
    with pytest.raises(ValidationError):
        CatalogEnvelope.model_validate(data)


@pytest.mark.parametrize(
    "field",
    [
        "source_reference",
        "access_conditions",
        "reuse_conditions",
        "permission_reference",
        "attribution",
        "last_checked",
    ],
)
def test_missing_source_permission_metadata_is_rejected(field: str) -> None:
    data = catalog()
    data["sources"][0].pop(field)
    with pytest.raises(ValidationError):
        CatalogEnvelope.model_validate(data)


@pytest.mark.parametrize(
    "change",
    [
        "source",
        "product",
        "evidence",
        "field",
        "disabled",
        "unverified",
        "identity-value",
        "cross-variant",
    ],
)
def test_invalid_cross_record_links_are_rejected(change: str) -> None:
    data = catalog()
    if change == "source":
        data["observations"][0]["source_id"] = "missing"
    if change == "product":
        data["observations"][0]["product_id"] = "missing"
    if change == "evidence":
        data["resolutions"][0]["evidence_ids"] = ["missing"]
    if change == "field":
        data["resolutions"][0]["evidence_ids"] = ["e-name"]
    if change == "disabled":
        data["sources"][0]["enabled"] = False
    if change == "unverified":
        data["observations"][0]["validation_status"] = "unverified"
    if change == "identity-value":
        data["observations"][0]["value"] = "Other brand"
    if change == "cross-variant":
        product = deepcopy(data["products"][0])
        product["product_id"] = "synthetic-100ml"
        product["variant"] = "formulation-a-100ml"
        data["products"].append(product)
        data["observations"][0]["product_id"] = "synthetic-100ml"
    with pytest.raises(ValidationError):
        CatalogEnvelope.model_validate(data)


def test_conflicting_observations_need_explicit_resolution() -> None:
    data = catalog()
    data["observations"].append(observation("price_paise", 90_000, suffix="-other"))
    resolution = next(r for r in data["resolutions"] if r["field_name"] == "price_paise")
    resolution["evidence_ids"] = ["e-price_paise", "e-price_paise-other"]
    with pytest.raises(ValidationError):
        CatalogEnvelope.model_validate(data)
    resolution["status"] = "unresolved"
    value = CatalogEnvelope.model_validate(data)
    assert (
        next(r for r in value.resolutions if r.field_name == "price_paise").status == "unresolved"
    )
    assert len([o for o in value.observations if o.field_name == "price_paise"]) == 2
    resolution["status"] = "selected"
    resolution["evidence_ids"] = ["e-price_paise-other"]
    CatalogEnvelope.model_validate(data)  # explicit selection; both observations retained


@pytest.mark.parametrize("field", ["source_id", "snapshot_id"])
def test_rating_and_count_need_the_same_source_snapshot(field: str) -> None:
    data = catalog()
    next(o for o in data["observations"] if o["field_name"] == "review_count")[field] = (
        "maker" if field == "source_id" else "other-snapshot"
    )
    with pytest.raises(ValidationError):
        CatalogEnvelope.model_validate(data)


@pytest.mark.parametrize("timestamp", ["2026-10-19T10:00:00", 1_000_000, True])
def test_naive_or_numeric_timestamps_are_rejected(timestamp: object) -> None:
    data = catalog()
    data["observations"][0]["retrieved_at"] = timestamp
    with pytest.raises(ValidationError):
        CatalogEnvelope.model_validate(data)


def test_offsets_normalize_to_utc_and_chronology_is_validated() -> None:
    data = catalog()
    data["observations"][0]["retrieved_at"] = datetime(
        2026, 10, 19, 15, 30, tzinfo=timezone(timedelta(hours=5.5))
    )
    value = CatalogEnvelope.model_validate(data)
    assert value.observations[0].retrieved_at == datetime(2026, 10, 19, 10, tzinfo=UTC)
    data["observations"][0]["verified_at"] = "2026-10-18T10:00:00Z"
    with pytest.raises(ValidationError):
        CatalogEnvelope.model_validate(data)


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong-version",
        "personal",
        "ambiguous-variant",
        "no-resolution",
        "price-currency",
        "unsafe-reference",
        "empty-selection",
    ],
)
def test_unsupported_or_ambiguous_envelopes_are_rejected(mutation: str) -> None:
    data = catalog()
    if mutation == "wrong-version":
        data["contract_version"] = "catalog-v2"
    if mutation == "personal":
        data["budget_inr"] = "800"
    if mutation == "ambiguous-variant":
        product = deepcopy(data["products"][0])
        product["product_id"] = "another-id"
        data["products"].append(product)
    if mutation == "no-resolution":
        data["resolutions"].pop()
    if mutation == "price-currency":
        next(o for o in data["observations"] if o["field_name"] == "price_paise")["currency"] = None
    if mutation == "unsafe-reference":
        data["observations"][0]["source_reference"] = "javascript:bad"
    if mutation == "empty-selection":
        data["resolutions"][0]["evidence_ids"] = []
    with pytest.raises(ValidationError):
        CatalogEnvelope.model_validate(data)


@pytest.mark.parametrize("status", ["yes", "no", "unknown"])
def test_all_sponsorship_states_are_preserved(status: str) -> None:
    data = catalog()
    next(o for o in data["observations"] if o["field_name"] == "sponsorship")["value"] = status
    value = CatalogEnvelope.model_validate(data)
    assert value.resolved_value("synthetic-50ml", "sponsorship") == status


def test_unresolved_evidence_never_becomes_a_canonical_value() -> None:
    data = catalog()
    next(r for r in data["resolutions"] if r["field_name"] == "price_paise")["status"] = (
        "unresolved"
    )
    value = CatalogEnvelope.model_validate(data)
    assert value.resolved_value("synthetic-50ml", "price_paise") is None
    assert value.resolved_value("missing-product", "rating") is None
    assert value.resolved_value("synthetic-50ml", "pack_size") == "50 ml"


def test_distinct_pack_cannot_reuse_product_identity() -> None:
    data = catalog()
    product = deepcopy(data["products"][0])
    product.update(variant="formulation-a-100ml", pack_size="100 ml")
    data["products"].append(product)
    with pytest.raises(ValidationError):
        CatalogEnvelope.model_validate(data)


def test_equal_selected_values_can_share_support_but_conflicts_remain_in_history() -> None:
    data = catalog()
    data["observations"].append(observation("price_paise", 80_000, suffix="-same"))
    next(r for r in data["resolutions"] if r["field_name"] == "price_paise")["evidence_ids"].append(
        "e-price_paise-same"
    )
    value = CatalogEnvelope.model_validate(data)
    assert value.resolved_value("synthetic-50ml", "price_paise") == 80_000


def test_disabled_unreferenced_source_is_not_assumed_approved() -> None:
    data = catalog()
    disabled = source("not-in-use")
    disabled["enabled"] = False
    data["sources"].append(disabled)
    assert CatalogEnvelope.model_validate(data).sources[-1].enabled is False


def test_schema_errors_do_not_expose_unrecognized_keys_or_payloads() -> None:
    data = catalog()
    data["observations"][0]["synthetic-private-key"] = "synthetic-private-value"
    with pytest.raises(ValidationError) as caught:
        CatalogEnvelope.model_validate(data)
    messages = CatalogEnvelope.validation_messages(caught.value)
    assert messages == ("observations: Remove unsupported fields.",)


def test_unknown_pack_size_cannot_hide_a_second_id_for_the_same_variant() -> None:
    data = catalog()
    second_id = "synthetic-duplicate-variant"
    product = deepcopy(data["products"][0])
    product.update(product_id=second_id, pack_size=None)
    data["products"].append(product)
    for original in list(data["observations"]):
        if original["field_name"] == "pack_size":
            continue
        other = deepcopy(original)
        other.update(product_id=second_id, evidence_id="other-" + original["evidence_id"])
        data["observations"].append(other)
    for original in list(data["resolutions"]):
        if original["field_name"] == "pack_size":
            continue
        other = deepcopy(original)
        other.update(
            product_id=second_id, evidence_ids=["other-" + e for e in original["evidence_ids"]]
        )
        data["resolutions"].append(other)
    with pytest.raises(ValidationError):
        CatalogEnvelope.model_validate(data)
