"""Session-only personal exclusion matching for ingredient declarations."""

from typing import Literal

from pydantic import Field

from schemas.common import Contract, Text
from schemas.ingredient_screening import IngredientRuleSet

PersonalExclusionStatus = Literal["matched", "requires_clarification"]


def _normalized(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _declarations(value: str | None) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip()) if value else ()


class PersonalExclusionFinding(Contract):
    requested_term: Text
    status: PersonalExclusionStatus
    matched_declarations: tuple[Text, ...] = ()


class PersonalExclusionResult(Contract):
    findings: tuple[PersonalExclusionFinding, ...] = ()
    matched_declarations: tuple[Text, ...] = Field(default=())
    excluded: bool


def evaluate_personal_exclusions(
    *, declaration: str | None, exclusions: tuple[str, ...], rules: IngredientRuleSet
) -> PersonalExclusionResult:
    """Match explicit ingredient terms only; unmatched language is never an exclusion."""
    declarations = _declarations(declaration)
    aliases = {
        _normalized(name): rule.rule_id
        for rule in rules.rules
        for name in (rule.canonical_ingredient, *rule.aliases)
    }
    declaration_rule_ids = {item: aliases.get(_normalized(item)) for item in declarations}
    findings: list[PersonalExclusionFinding] = []
    all_matches: set[str] = set()
    for raw_term in exclusions:
        term = raw_term.strip()
        if not term:
            continue
        normalized = _normalized(term)
        requested_rule_id = aliases.get(normalized)
        matches = tuple(
            item
            for item in declarations
            if _normalized(item) == normalized
            or (requested_rule_id is not None and declaration_rule_ids[item] == requested_rule_id)
        )
        if matches:
            all_matches.update(matches)
            findings.append(
                PersonalExclusionFinding(
                    requested_term=term,
                    status="matched",
                    matched_declarations=matches,
                )
            )
        else:
            findings.append(
                PersonalExclusionFinding(
                    requested_term=term,
                    status="requires_clarification",
                )
            )
    return PersonalExclusionResult(
        findings=tuple(findings),
        matched_declarations=tuple(item for item in declarations if item in all_matches),
        excluded=bool(all_matches),
    )
