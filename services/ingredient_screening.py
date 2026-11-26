"""Deterministic, limited ingredient-rule evaluation without personal data."""

from hashlib import sha256
from typing import Literal, cast

from schemas.catalog import CatalogEnvelope, FactObservation, FactResolution
from schemas.ingredient_screening import (
    Eligibility,
    FindingStatus,
    IngredientFinding,
    IngredientRule,
    IngredientRuleSet,
    IngredientScreeningResult,
    ScreeningInput,
)


def _normalized(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _declarations(value: str | None) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip()) if value else ()


def _fingerprint(value: ScreeningInput | IngredientRuleSet) -> str:
    return sha256(value.model_dump_json().encode("utf-8")).hexdigest()


def _finding(rule: IngredientRule, matched: str, screening: ScreeningInput) -> IngredientFinding:
    checked = tuple(
        condition for condition in rule.required_conditions if condition in screening.conditions
    )
    failed = tuple(
        condition
        for condition in rule.required_conditions
        if condition in screening.failed_conditions
    )
    missing = tuple(
        condition
        for condition in rule.required_conditions
        if condition not in screening.conditions and condition not in screening.failed_conditions
    )
    names = {_normalized(name) for name in (rule.canonical_ingredient, *rule.aliases)}
    concentrations = tuple(
        item.percent for item in screening.concentrations if _normalized(item.name) in names
    )
    concentration = concentrations[0] if len(concentrations) == 1 else None
    if rule.max_concentration_percent is not None:
        if concentration is None:
            missing += ("concentration_percent",)
        elif concentration > rule.max_concentration_percent:
            failed += ("concentration_percent",)
        else:
            checked += ("concentration_percent",)
    if rule.rule_type == "prohibited":
        status: FindingStatus = "prohibited"
    elif failed:
        status = "restricted_failed"
    elif missing:
        status = "requires_verification"
    else:
        status = "restricted_satisfied"
    return IngredientFinding(
        rule_id=rule.rule_id,
        canonical_ingredient=rule.canonical_ingredient,
        matched_declaration=matched,
        status=status,
        source_reference=rule.source_reference,
        source_section=rule.source_section,
        rule_version=rule.version,
        checked_on=rule.checked_on,
        categories=rule.categories,
        checked_conditions=checked,
        failed_conditions=failed,
        missing_conditions=missing,
        observed_concentration_percent=concentration,
        max_concentration_percent=rule.max_concentration_percent,
    )


def evaluate_ingredients(
    screening: ScreeningInput, rules: IngredientRuleSet
) -> IngredientScreeningResult:
    """Evaluate only curated rules; absence means no issue in this limited rule set."""
    normalized_rules = {
        _normalized(name): rule
        for rule in rules.rules
        for name in (rule.canonical_ingredient, *rule.aliases)
    }
    findings = tuple(
        _finding(normalized_rules[_normalized(item)], item, screening)
        for item in _declarations(screening.declaration)
        if _normalized(item) in normalized_rules
        and screening.category in normalized_rules[_normalized(item)].categories
    )
    incomplete = screening.completeness != "complete" or screening.declaration is None
    excluded = any(finding.status in ("prohibited", "restricted_failed") for finding in findings)
    requires_verification = incomplete or any(
        finding.status == "requires_verification" for finding in findings
    )
    eligibility: Eligibility = (
        "excluded"
        if excluded
        else "requires_verification"
        if requires_verification
        else "eligible_within_checks"
    )
    return IngredientScreeningResult(
        product_id=screening.product_id,
        evidence_id=screening.evidence_id,
        evidence_version=screening.evidence_version,
        evidence_fingerprint=_fingerprint(screening),
        rule_set_id=rules.rule_set_id,
        rule_set_version=rules.version,
        rule_set_fingerprint=_fingerprint(rules),
        findings=findings,
        eligibility=eligibility,
        unresolved_reason_codes=(
            ("conflicting_ingredient_evidence",)
            if screening.completeness == "conflicting"
            else ("incomplete_ingredient_evidence",)
            if incomplete
            else ()
        ),
    )


def result_is_current(
    result: IngredientScreeningResult, screening: ScreeningInput, rules: IngredientRuleSet
) -> bool:
    """A caller may reuse only public results tied to current evidence and rule versions."""
    return (
        result.product_id == screening.product_id
        and result.evidence_id == screening.evidence_id
        and result.evidence_version == screening.evidence_version
        and result.evidence_fingerprint == _fingerprint(screening)
        and result.rule_set_id == rules.rule_set_id
        and result.rule_set_version == rules.version
        and result.rule_set_fingerprint == _fingerprint(rules)
    )


def screening_input_from_catalog(catalog: CatalogEnvelope, product_id: str) -> ScreeningInput:
    """Build a conservative public screening input from explicitly resolved catalog facts."""
    product = next(item for item in catalog.products if item.product_id == product_id)
    resolutions = {
        item.field_name: item for item in catalog.resolutions if item.product_id == product_id
    }
    observations = {item.evidence_id: item for item in catalog.observations}
    declaration_resolution = resolutions.get("ingredient_declaration")
    completeness_resolution = resolutions.get("ingredient_completeness")

    def selected(resolution: FactResolution | None) -> FactObservation | None:
        if resolution is None or resolution.status != "selected":
            return None
        return observations[resolution.evidence_ids[0]]

    declaration_observation = selected(declaration_resolution)
    completeness_observation = selected(completeness_resolution)
    declaration = (
        declaration_observation.value
        if declaration_observation and isinstance(declaration_observation.value, str)
        else None
    )
    completeness: Literal["complete", "partial", "unknown", "conflicting"] = "unknown"
    if declaration_resolution is not None and declaration_resolution.status == "unresolved":
        completeness = "conflicting"
    if (
        completeness_observation is not None
        and isinstance(completeness_observation.value, str)
        and completeness_observation.value in {"complete", "partial", "unknown"}
    ):
        completeness = cast(
            Literal["complete", "partial", "unknown"], completeness_observation.value
        )
    if declaration_observation is None:
        return ScreeningInput(
            product_id=product_id,
            evidence_id=f"unresolved-ingredients:{product_id}",
            evidence_version="unresolved",
            category=product.category,
            declaration=None,
            completeness=completeness,
        )
    return ScreeningInput(
        product_id=product_id,
        evidence_id=declaration_observation.evidence_id,
        evidence_version=declaration_observation.content_version,
        category=product.category,
        declaration=declaration,
        completeness=completeness,
    )
