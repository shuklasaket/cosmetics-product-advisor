"""US-038 deterministic source precedence, freshness, and qualification decisions."""

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import Literal

from schemas.catalog import CatalogEnvelope, FactName, FactObservation
from schemas.common import Contract, Identifier

Freshness = Literal["fresh", "stale", "unknown"]
QualificationReason = Literal[
    "stale_availability",
    "stale_price",
    "unresolved_availability",
    "unresolved_identity",
    "unresolved_ingredient",
    "unresolved_price",
]

_PRECEDENCE: dict[FactName, str] = {
    "availability": "retailer",
    "ingredient_declaration": "manufacturer",
    "ingredient_completeness": "manufacturer",
    "pack_size": "manufacturer",
    "price_paise": "retailer",
}
_CRITICAL_FIELDS: tuple[FactName, ...] = (
    "availability",
    "price_paise",
    "ingredient_declaration",
    "ingredient_completeness",
    "brand",
    "name",
    "category",
    "variant",
)
_UNRESOLVED_REASONS: dict[str, QualificationReason] = {
    "availability": "unresolved_availability",
    "price_paise": "unresolved_price",
    "ingredient_declaration": "unresolved_ingredient",
    "ingredient_completeness": "unresolved_ingredient",
    "brand": "unresolved_identity",
    "name": "unresolved_identity",
    "category": "unresolved_identity",
    "variant": "unresolved_identity",
}


class FactPolicy(Contract):
    product_id: Identifier
    field_name: FactName
    selected_evidence_id: Identifier | None = None
    conflicting_evidence_ids: tuple[Identifier, ...] = ()
    freshness: Freshness
    verified_at: datetime | None = None


class ProductQualification(Contract):
    product_id: Identifier
    qualified: bool
    reason_codes: tuple[QualificationReason, ...] = ()


class CatalogPolicyResult(Contract):
    facts: tuple[FactPolicy, ...] = ()
    qualifications: tuple[ProductQualification, ...] = ()

    def fact(self, product_id: str, field_name: FactName) -> FactPolicy:
        return next(
            item
            for item in self.facts
            if (item.product_id, item.field_name) == (product_id, field_name)
        )

    def qualification(self, product_id: str) -> ProductQualification:
        return next(item for item in self.qualifications if item.product_id == product_id)


def _freshness(observation: FactObservation | None, now: datetime) -> Freshness:
    if observation is None:
        return "unknown"
    window = timedelta(days=7 if observation.field_name in {"availability", "price_paise"} else 30)
    return "fresh" if now - observation.verified_at <= window else "stale"


def _preferred_observation(
    observations: tuple[FactObservation, ...], source_types: Mapping[str, str]
) -> FactObservation | None:
    if not observations:
        return None
    field = observations[0].field_name
    preferred_type = _PRECEDENCE.get(field)
    if preferred_type is not None:
        preferred = [
            item for item in observations if source_types[item.source_id] == preferred_type
        ]
        if len(preferred) == 1:
            return preferred[0]
        if len(preferred) > 1:
            return None
    # Open Beauty Facts is supplemental: it only supplies a field when no higher-priority
    # approved source supplies it and exactly one candidate remains.
    obf = [item for item in observations if item.source_id == "open-beauty-facts"]
    if len(obf) == 1 and len(observations) == 1:
        return obf[0]
    return None


def evaluate_catalog(catalog: CatalogEnvelope, *, now: datetime) -> CatalogPolicyResult:
    """Assess evidence without changing the explicit resolutions or observation history."""
    current = now.astimezone(UTC)
    source_types = {source.source_id: source.source_type for source in catalog.sources}
    observations_by_key: dict[tuple[str, FactName], list[FactObservation]] = {}
    for observation in catalog.observations:
        observations_by_key.setdefault((observation.product_id, observation.field_name), []).append(
            observation
        )
    resolutions = {(item.product_id, item.field_name): item for item in catalog.resolutions}
    facts: list[FactPolicy] = []
    qualifications: list[ProductQualification] = []
    for product in catalog.products:
        policies: dict[FactName, FactPolicy] = {}
        for (product_id, field), items in observations_by_key.items():
            if product_id != product.product_id:
                continue
            evidence = tuple(items)
            resolution = resolutions[(product_id, field)]
            selected: FactObservation | None = None
            if resolution.status == "selected":
                selected = next(
                    item for item in evidence if item.evidence_id == resolution.evidence_ids[0]
                )
            else:
                selected = _preferred_observation(evidence, source_types)
            conflicts = tuple(
                item.evidence_id
                for item in evidence
                if selected is not None
                and item.evidence_id != selected.evidence_id
                and item.value != selected.value
            )
            policy = FactPolicy(
                product_id=product_id,
                field_name=field,
                selected_evidence_id=selected.evidence_id if selected else None,
                conflicting_evidence_ids=conflicts,
                freshness=_freshness(selected, current),
                verified_at=selected.verified_at if selected else None,
            )
            facts.append(policy)
            policies[field] = policy
        reasons: list[QualificationReason] = []
        for field in _CRITICAL_FIELDS:
            critical_policy = policies.get(field)
            unresolved = (
                critical_policy is None
                or critical_policy.selected_evidence_id is None
                or bool(critical_policy.conflicting_evidence_ids)
            )
            if unresolved:
                reason = _UNRESOLVED_REASONS[field]
                if reason not in reasons:
                    reasons.append(reason)
            if (
                field in {"availability", "price_paise"}
                and critical_policy
                and critical_policy.freshness == "stale"
            ):
                stale: QualificationReason = (
                    "stale_availability" if field == "availability" else "stale_price"
                )
                reasons.append(stale)
        qualifications.append(
            ProductQualification(
                product_id=product.product_id,
                qualified=not reasons,
                reason_codes=tuple(sorted(set(reasons))),
            )
        )
    return CatalogPolicyResult(facts=tuple(facts), qualifications=tuple(qualifications))
