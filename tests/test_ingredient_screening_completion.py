"""Remaining US-056 acceptance cases use synthetic rules and declarations only."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from schemas.ingredient_screening import (
    IngredientConcentration,
    IngredientRule,
    IngredientRuleSet,
    ScreeningInput,
)
from services.ingredient_screening import evaluate_ingredients, result_is_current


def rule(**changes: object) -> IngredientRule:
    values = {
        "rule_id": "synthetic-restriction",
        "canonical_ingredient": "Synthetic B",
        "aliases": ("Synthetic-B",),
        "rule_type": "restricted",
        "categories": ("sunscreen",),
        "required_conditions": ("leave_on",),
        "source_reference": "https://example.com/synthetic-rules#b",
        "source_section": "Schedule example, row B",
        "version": "v1",
        "checked_on": date(2026, 11, 26),
    }
    values.update(changes)
    return IngredientRule.model_validate(values)


def rule_set(**changes: object) -> IngredientRuleSet:
    values = {"rule_set_id": "synthetic-india", "version": "v1", "rules": (rule(),)}
    values.update(changes)
    return IngredientRuleSet.model_validate(values)


def screening(**changes: object) -> ScreeningInput:
    values = {
        "product_id": "synthetic-product",
        "evidence_id": "synthetic-evidence",
        "evidence_version": "sha256:one",
        "category": "sunscreen",
        "declaration": "Water, Synthetic-B",
        "completeness": "complete",
    }
    values.update(changes)
    return ScreeningInput.model_validate(values)


def test_rejects_missing_scope_provenance_and_ambiguous_aliases() -> None:
    for changes in ({"categories": ()}, {"source_section": " "}, {"checked_on": None}):
        with pytest.raises(ValidationError):
            rule(**changes)
    with pytest.raises(ValidationError):
        rule_set(rules=(rule(), rule(rule_id="another", aliases=("synthetic b",))))


def test_restriction_conditions_have_satisfied_failed_and_unknown_outcomes() -> None:
    rules = rule_set()
    satisfied = evaluate_ingredients(screening(conditions=("leave_on",)), rules)
    failed = evaluate_ingredients(screening(failed_conditions=("leave_on",)), rules)
    unknown = evaluate_ingredients(screening(), rules)

    assert satisfied.findings[0].status == "restricted_satisfied"
    assert satisfied.findings[0].checked_conditions == ("leave_on",)
    assert satisfied.eligibility == "eligible_within_checks"
    assert failed.findings[0].status == "restricted_failed"
    assert failed.findings[0].failed_conditions == ("leave_on",)
    assert failed.eligibility == "excluded"
    assert unknown.findings[0].status == "requires_verification"
    assert unknown.findings[0].missing_conditions == ("leave_on",)
    assert unknown.eligibility == "requires_verification"


def test_concentration_boundary_and_missing_value_are_conservative() -> None:
    rules = rule_set(rules=(rule(required_conditions=(), max_concentration_percent=Decimal("2")),))
    within = evaluate_ingredients(
        screening(concentrations=(IngredientConcentration(name="Synthetic B", percent="2"),)),
        rules,
    )
    over = evaluate_ingredients(
        screening(concentrations=(IngredientConcentration(name="Synthetic B", percent="2.01"),)),
        rules,
    )
    missing = evaluate_ingredients(screening(), rules)

    assert within.findings[0].status == "restricted_satisfied"
    assert within.eligibility == "eligible_within_checks"
    assert over.findings[0].status == "restricted_failed"
    assert over.eligibility == "excluded"
    assert missing.findings[0].status == "requires_verification"
    assert "concentration_percent" in missing.findings[0].missing_conditions
    assert missing.eligibility == "requires_verification"


def test_conflicting_concentration_alias_evidence_remains_unresolved() -> None:
    rules = rule_set(rules=(rule(required_conditions=(), max_concentration_percent=Decimal("2")),))
    result = evaluate_ingredients(
        screening(
            concentrations=(
                IngredientConcentration(name="Synthetic B", percent="1"),
                IngredientConcentration(name="Synthetic-B", percent="3"),
            )
        ),
        rules,
    )

    assert result.findings[0].status == "requires_verification"
    assert result.findings[0].observed_concentration_percent is None
    assert result.findings[0].missing_conditions == ("concentration_percent",)
    assert result.eligibility == "requires_verification"


def test_category_scope_and_missing_or_conflicting_declarations() -> None:
    rules = rule_set()
    outside = evaluate_ingredients(screening(category="moisturiser"), rules)
    missing = evaluate_ingredients(screening(declaration=None, completeness="unknown"), rules)
    conflicting = evaluate_ingredients(screening(completeness="conflicting"), rules)
    falsely_complete = evaluate_ingredients(
        screening(declaration=None, completeness="complete"), rules
    )

    assert outside.findings == ()
    assert outside.eligibility == "eligible_within_checks"
    assert missing.eligibility == "requires_verification"
    assert conflicting.eligibility == "requires_verification"
    assert falsely_complete.eligibility == "requires_verification"
    assert "incomplete_ingredient_evidence" in missing.unresolved_reason_codes
    assert "conflicting_ingredient_evidence" in conflicting.unresolved_reason_codes


def test_result_versions_invalidate_reuse_and_retain_rule_provenance() -> None:
    current_input = screening(conditions=("leave_on",))
    rules = rule_set()
    result = evaluate_ingredients(current_input, rules)

    assert result.findings[0].checked_on == date(2026, 11, 26)
    assert result.findings[0].rule_version == "v1"
    assert result.findings[0].source_section == "Schedule example, row B"
    assert result_is_current(result, current_input, rules)
    assert not result_is_current(result, screening(evidence_version="sha256:two"), rules)
    assert not result_is_current(result, current_input, rule_set(version="v2"))
    assert not result_is_current(result, screening(declaration="Synthetic B"), rules)
    assert not result_is_current(
        result,
        current_input,
        rule_set(rules=(rule(max_concentration_percent=Decimal("2")),)),
    )
