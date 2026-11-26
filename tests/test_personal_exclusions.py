"""US-057 session-only personal exclusion evaluation."""

from schemas.ingredient_screening import IngredientRuleSet
from services.personal_exclusions import evaluate_personal_exclusions


def rules() -> IngredientRuleSet:
    return IngredientRuleSet.model_validate(
        {
            "rule_set_id": "limited-rules",
            "version": "v1",
            "rules": [
                {
                    "rule_id": "hexachlorophene",
                    "canonical_ingredient": "Hexachlorophene",
                    "aliases": ["Hexachlorophene USP"],
                    "rule_type": "prohibited",
                    "categories": ["sunscreen", "moisturiser"],
                    "source_reference": "https://example.com/rules",
                    "source_section": "section 1",
                    "version": "v1",
                    "checked_on": "2026-11-26",
                }
            ],
        }
    )


def test_exact_and_curated_alias_matches_are_excluded_separately_from_rules() -> None:
    result = evaluate_personal_exclusions(
        declaration="Water, Hexachlorophene USP, Glycerin",
        exclusions=("glycerin", "Hexachlorophene"),
        rules=rules(),
    )

    assert result.matched_declarations == ("Hexachlorophene USP", "Glycerin")
    assert [finding.status for finding in result.findings] == ["matched", "matched"]
    assert result.excluded


def test_unmatched_general_preference_requires_clarification_without_exclusion() -> None:
    result = evaluate_personal_exclusions(
        declaration="Water, Glycerin",
        exclusions=("lightweight",),
        rules=rules(),
    )

    assert result.matched_declarations == ()
    assert result.findings[0].status == "requires_clarification"
    assert not result.excluded
