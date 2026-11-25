"""Deterministic, limited ingredient-rule evaluation without personal data."""

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


def _finding(rule: IngredientRule, matched: str, conditions: set[str]) -> IngredientFinding:
    missing = tuple(
        condition for condition in rule.required_conditions if condition not in conditions
    )
    if rule.rule_type == "prohibited":
        status: FindingStatus = "prohibited"
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
        missing_conditions=missing,
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
    conditions = set(screening.conditions)
    findings = tuple(
        _finding(normalized_rules[_normalized(item)], item, conditions)
        for item in _declarations(screening.declaration)
        if _normalized(item) in normalized_rules
    )
    incomplete = screening.completeness != "complete"
    excluded = any(finding.status == "prohibited" for finding in findings)
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
        rule_set_id=rules.rule_set_id,
        rule_set_version=rules.version,
        findings=findings,
        eligibility=eligibility,
        unresolved_reason_codes=("incomplete_ingredient_evidence",) if incomplete else (),
    )
