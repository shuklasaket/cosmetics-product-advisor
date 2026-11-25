"""US-056 deterministic ingredient-screening acceptance checks."""

from datetime import date

from schemas.ingredient_screening import IngredientRule, IngredientRuleSet, ScreeningInput
from services.ingredient_screening import evaluate_ingredients


def rules() -> IngredientRuleSet:
    return IngredientRuleSet(
        rule_set_id="synthetic-india-v1",
        version="v1",
        rules=(
            IngredientRule(
                rule_id="rule-prohibited-a",
                canonical_ingredient="Synthetic A",
                aliases=("Synthetic-A",),
                rule_type="prohibited",
                categories=("sunscreen",),
                source_reference="https://example.com/rules#synthetic-a",
                source_section="section 1",
                version="v1",
                checked_on=date(2026, 11, 25),
            ),
            IngredientRule(
                rule_id="rule-restricted-b",
                canonical_ingredient="Synthetic B",
                rule_type="restricted",
                categories=("sunscreen",),
                required_conditions=("rinse_off",),
                source_reference="https://example.com/rules#synthetic-b",
                source_section="section 2",
                version="v1",
                checked_on=date(2026, 11, 25),
            ),
        ),
    )


def test_alias_match_preserves_declaration_and_excludes_prohibited_rule() -> None:
    result = evaluate_ingredients(
        ScreeningInput(
            product_id="synthetic-product",
            evidence_id="ingredient-evidence-v1",
            evidence_version="sha256:one",
            category="sunscreen",
            declaration="Water, synthetic-a, Glycerin",
            completeness="complete",
        ),
        rules(),
    )

    assert result.eligibility == "excluded"
    assert result.rule_set_version == "v1"
    assert result.evidence_version == "sha256:one"
    assert result.findings[0].matched_declaration == "synthetic-a"
    assert result.findings[0].canonical_ingredient == "Synthetic A"
    assert result.findings[0].status == "prohibited"


def test_missing_restriction_condition_and_partial_evidence_require_verification() -> None:
    result = evaluate_ingredients(
        ScreeningInput(
            product_id="synthetic-product",
            evidence_id="ingredient-evidence-v1",
            evidence_version="sha256:one",
            category="sunscreen",
            declaration="Synthetic B",
            completeness="partial",
        ),
        rules(),
    )

    assert result.eligibility == "requires_verification"
    assert result.findings[0].status == "requires_verification"
    assert result.findings[0].missing_conditions == ("rinse_off",)
    assert result.unresolved_reason_codes == ("incomplete_ingredient_evidence",)


def test_complete_no_match_is_limited_eligibility_and_rules_require_provenance() -> None:
    result = evaluate_ingredients(
        ScreeningInput(
            product_id="synthetic-product",
            evidence_id="ingredient-evidence-v1",
            evidence_version="sha256:one",
            category="sunscreen",
            declaration="Water, Glycerin",
            completeness="complete",
        ),
        rules(),
    )

    assert result.eligibility == "eligible_within_checks"
    assert result.findings == ()
