"""Versioned evidence boundaries, not a database, collector or import command."""

from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any, Literal, Self, cast
from urllib.parse import urlsplit

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BeforeValidator,
    Field,
    StrictBool,
    TypeAdapter,
    ValidationInfo,
    field_validator,
    model_validator,
)

from schemas.common import Category, Contract, Identifier, SkinType, Text


def timestamp_input(value: object) -> object:
    if not isinstance(value, (str, datetime)):
        raise ValueError("Supply an ISO timestamp with timezone, not a numeric timestamp.")
    return value


UtcTimestamp = Annotated[
    AwareDatetime,
    BeforeValidator(timestamp_input),
    AfterValidator(lambda value: value.astimezone(UTC)),
]
NonNegativeInt = Annotated[int, Field(strict=True, ge=0)]
FactName = Literal[
    "brand",
    "name",
    "category",
    "variant",
    "pack_size",
    "availability",
    "price_paise",
    "skin_type_claims",
    "rating",
    "review_count",
    "ingredient_declaration",
    "ingredient_completeness",
    "sponsorship",
]


def reference(value: str) -> str:
    if value.startswith("document:") and value.removeprefix("document:").strip():
        return value
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme == "https"
            and parsed.hostname
            and not parsed.username
            and not parsed.password
        ):
            # Validate port syntax as well as host presence; nothing is fetched here.
            _ = parsed.port
            if not any(c.isspace() for c in value) and "\\" not in value:
                return value
    except ValueError:
        pass
    raise ValueError("Supply an HTTPS source URL without credentials or a document: reference.")


Reference = Annotated[Text, AfterValidator(reference)]


def finite_decimal(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError("Supply a finite decimal rating or scale value.")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise ValueError("Supply a finite decimal rating or scale value.") from None
    if not result.is_finite():
        raise ValueError("Supply a finite decimal rating or scale value.")
    return result


RatingNumber = Annotated[Decimal, BeforeValidator(finite_decimal)]


class Rating(Contract):
    score: RatingNumber
    scale_min: RatingNumber = Field(ge=0)
    scale_max: RatingNumber

    @model_validator(mode="after")
    def check_scale(self) -> Self:
        if self.scale_max <= self.scale_min or not self.scale_min <= self.score <= self.scale_max:
            raise ValueError("Rating must fall within an explicit increasing non-negative scale.")
        return self


class Product(Contract):
    """One exact formulation/pack variant; these identity facts also need evidence."""

    product_id: Identifier
    brand: Text
    name: Text
    category: Category
    variant: Text
    pack_size: Text | None = None


class Source(Contract):
    source_id: Identifier
    source_type: Literal["manufacturer", "retailer", "dataset", "document"]
    source_reference: Reference
    access_conditions: Text
    reuse_conditions: Text
    permission_reference: Reference
    attribution: Text
    last_checked: UtcTimestamp
    enabled: StrictBool


# Dispatch on field_name before accepting a value. In particular, strings/bools/floats
# cannot silently become integer paise or counts. JSON arrays become immutable tuples.
FACT_ANNOTATIONS: dict[str, Any] = {
    "brand": Text | None,
    "name": Text | None,
    "category": Category | None,
    "variant": Text | None,
    "pack_size": Text | None,
    "availability": tuple[Text, ...] | None,
    "price_paise": NonNegativeInt | None,
    "skin_type_claims": tuple[SkinType, ...] | None,
    "rating": Rating | None,
    "review_count": NonNegativeInt | None,
    "ingredient_declaration": Text | None,
    "ingredient_completeness": Literal["complete", "partial", "unknown"] | None,
    "sponsorship": Literal["yes", "no", "unknown"] | None,
}
FACT_TYPES = {field: TypeAdapter(annotation) for field, annotation in FACT_ANNOTATIONS.items()}
FactValue = Text | NonNegativeInt | tuple[Text, ...] | Rating | None


class FactObservation(Contract):
    evidence_id: Identifier
    product_id: Identifier
    source_id: Identifier
    field_name: FactName
    value: FactValue
    country: Literal["India"] | None = None
    currency: Literal["INR"] | None = None
    source_reference: Reference
    retrieved_at: UtcTimestamp
    verified_at: UtcTimestamp
    content_version: Text
    snapshot_id: Identifier
    validation_status: Literal["verified", "unverified"]

    @field_validator("value", mode="before")
    @classmethod
    def check_value(cls, value: object, info: ValidationInfo) -> FactValue:
        field = info.data.get("field_name")
        if field not in FACT_TYPES:
            raise ValueError("Supply a supported fact field before its typed value.")
        return cast(FactValue, FACT_TYPES[field].validate_python(value))

    @model_validator(mode="after")
    def check_context(self) -> Self:
        if self.verified_at < self.retrieved_at:
            raise ValueError("Verification timestamp cannot precede retrieval.")
        if self.field_name == "price_paise":
            if self.country != "India" or self.currency != "INR":
                raise ValueError("Price observations require explicit India and INR context.")
        elif self.country is not None or self.currency is not None:
            raise ValueError("Country/currency context is only supported on price observations.")
        return self


class FactResolution(Contract):
    product_id: Identifier
    field_name: FactName
    status: Literal["selected", "unresolved"]
    evidence_ids: tuple[Identifier, ...] = Field(min_length=1)
    policy_version: Literal["explicit-selection-v1"]

    @field_validator("evidence_ids")
    @classmethod
    def unique_evidence(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("A resolution cannot repeat an evidence ID.")
        return value


def unique_records[T](records: Iterable[T], attribute: str) -> dict[str, T]:
    result: dict[str, T] = {}
    for record in records:
        key: str = getattr(record, attribute)
        if key in result:
            raise ValueError("Duplicate record identity; review variant mapping or repeated input.")
        result[key] = record
    return result


class CatalogEnvelope(Contract):
    """Validate the complete in-memory batch before any downstream write."""

    contract_version: Literal["catalog-v1"]
    products: tuple[Product, ...]
    sources: tuple[Source, ...]
    observations: tuple[FactObservation, ...]
    resolutions: tuple[FactResolution, ...]

    @model_validator(mode="after")
    def check_links(self) -> Self:
        products = unique_records(self.products, "product_id")
        sources = unique_records(self.sources, "source_id")
        evidence = unique_records(self.observations, "evidence_id")
        identities = [(p.brand, p.name, p.category, p.variant) for p in self.products]
        if len(identities) != len(set(identities)):
            raise ValueError("One exact variant cannot have multiple product IDs in a batch.")
        resolved: dict[tuple[str, str], FactResolution] = {}
        for item in self.observations:
            if item.product_id not in products or item.source_id not in sources:
                raise ValueError("Observation must link to a registered product and source.")
            if not sources[item.source_id].enabled:
                raise ValueError("Observation source must be enabled for use.")
        for resolution in self.resolutions:
            key = (resolution.product_id, resolution.field_name)
            if resolution.product_id not in products or key in resolved:
                raise ValueError(
                    "Resolution must uniquely identify a registered product and field."
                )
            selected: list[FactObservation] = []
            for evidence_id in resolution.evidence_ids:
                candidate = evidence.get(evidence_id)
                if candidate is None or (candidate.product_id, candidate.field_name) != key:
                    raise ValueError("Resolution evidence must match its exact product and field.")
                selected.append(candidate)
            if resolution.status == "selected":
                if any(item.validation_status != "verified" for item in selected):
                    raise ValueError("Canonical facts require verified evidence.")
                if any(item.value != selected[0].value for item in selected):
                    raise ValueError(
                        "Conflicting values require explicit selection or unresolved status."
                    )
            resolved[key] = resolution
        for item in self.observations:
            if (item.product_id, item.field_name) not in resolved:
                raise ValueError("Every observed field requires an explicit resolution status.")
        for product in self.products:
            for field in ("brand", "name", "category", "variant", "pack_size"):
                expected = getattr(product, field)
                if expected is not None:
                    identity_resolution = resolved.get((product.product_id, field))
                    if identity_resolution is None or identity_resolution.status != "selected":
                        raise ValueError(
                            "Non-null product identity requires selected field evidence."
                        )
                    if evidence[identity_resolution.evidence_ids[0]].value != expected:
                        raise ValueError("Product identity disagrees with selected evidence.")
                elif (product.product_id, field) in resolved:
                    resolution = resolved[(product.product_id, field)]
                    if (
                        resolution.status == "selected"
                        and evidence[resolution.evidence_ids[0]].value is not None
                    ):
                        raise ValueError("Unknown pack size cannot conceal a selected known value.")
            rating_evidence: list[FactObservation] = []
            for field in ("rating", "review_count"):
                rating_resolution = resolved.get((product.product_id, field))
                if rating_resolution is not None and rating_resolution.status == "selected":
                    rating_evidence.extend(
                        evidence[eid]
                        for eid in rating_resolution.evidence_ids
                        if evidence[eid].value is not None
                    )
            if len({(e.source_id, e.snapshot_id) for e in rating_evidence}) > 1:
                raise ValueError("Rating and count require one compatible source/variant snapshot.")
        return self

    def resolved_value(self, product_id: str, field_name: FactName) -> FactValue:
        """Unknown/unresolved fields return None; never choose an observation implicitly."""
        for resolution in self.resolutions:
            if (resolution.product_id, resolution.field_name) == (
                product_id,
                field_name,
            ) and resolution.status == "selected":
                return next(
                    item.value
                    for item in self.observations
                    if item.evidence_id == resolution.evidence_ids[0]
                )
        return None
