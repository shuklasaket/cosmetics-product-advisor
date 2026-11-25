"""Typed, synthetic-first ingredient-screening contracts for PRD 03."""

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal

from pydantic import BeforeValidator, Field, field_validator, model_validator

from schemas.catalog import Reference
from schemas.common import Category, Contract, Identifier, Text

RuleType = Literal["prohibited", "restricted"]
FindingStatus = Literal[
    "prohibited", "restricted_satisfied", "restricted_failed", "requires_verification"
]
Eligibility = Literal["eligible_within_checks", "excluded", "requires_verification"]
ReasonCode = Literal["incomplete_ingredient_evidence", "conflicting_ingredient_evidence"]


def _normalized(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def _percentage(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError("Supply an exact concentration percentage.")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise ValueError("Supply an exact concentration percentage.") from None
    if not result.is_finite() or not 0 <= result <= 100:
        raise ValueError("Concentration percentage must be between 0 and 100.")
    return result


Percentage = Annotated[Decimal, BeforeValidator(_percentage)]


class IngredientRule(Contract):
    rule_id: Identifier
    canonical_ingredient: Text
    aliases: tuple[Text, ...] = ()
    rule_type: RuleType
    categories: tuple[Category, ...] = Field(min_length=1)
    required_conditions: tuple[Text, ...] = ()
    max_concentration_percent: Percentage | None = None
    source_reference: Reference
    source_section: Text
    version: Text
    checked_on: date

    @field_validator("aliases", "categories", "required_conditions")
    @classmethod
    def unique_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("Rule aliases, categories, and conditions must be unique.")
        return value

    @model_validator(mode="after")
    def check_rule(self) -> "IngredientRule":
        if self.rule_type == "prohibited" and (
            self.required_conditions or self.max_concentration_percent is not None
        ):
            raise ValueError("Prohibited rules cannot require conditions.")
        if self.rule_type == "restricted" and not (
            self.required_conditions or self.max_concentration_percent is not None
        ):
            raise ValueError("Restricted rules need an explicit checkable condition.")
        return self


class IngredientRuleSet(Contract):
    rule_set_id: Identifier
    version: Text
    rules: tuple[IngredientRule, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_rules(self) -> "IngredientRuleSet":
        if len({rule.rule_id for rule in self.rules}) != len(self.rules):
            raise ValueError("A rule set cannot repeat rule IDs.")
        mapped_names: dict[str, str] = {}
        for rule in self.rules:
            for name in (rule.canonical_ingredient, *rule.aliases):
                normalized = _normalized(name)
                if normalized in mapped_names and mapped_names[normalized] != rule.rule_id:
                    raise ValueError("A rule set cannot map one normalized name to multiple rules.")
                mapped_names[normalized] = rule.rule_id
        return self


class ScreeningInput(Contract):
    product_id: Identifier
    evidence_id: Identifier
    evidence_version: Text
    category: Category
    declaration: Text | None = None
    completeness: Literal["complete", "partial", "unknown", "conflicting"]
    conditions: tuple[Text, ...] = ()
    failed_conditions: tuple[Text, ...] = ()
    concentrations: tuple["IngredientConcentration", ...] = ()

    @model_validator(mode="after")
    def check_evidence(self) -> "ScreeningInput":
        if set(self.conditions) & set(self.failed_conditions):
            raise ValueError("A condition cannot be both satisfied and failed.")
        if len(self.conditions) != len(set(self.conditions)) or len(self.failed_conditions) != len(
            set(self.failed_conditions)
        ):
            raise ValueError("Condition evidence cannot repeat a condition.")
        return self


class IngredientConcentration(Contract):
    """Explicit measured or sourced concentration; declaration order supplies no value."""

    name: Text
    percent: Percentage


class IngredientFinding(Contract):
    rule_id: Identifier
    canonical_ingredient: Text
    matched_declaration: Text
    status: FindingStatus
    source_reference: Reference
    source_section: Text
    rule_version: Text
    checked_on: date
    categories: tuple[Category, ...]
    checked_conditions: tuple[Text, ...] = ()
    failed_conditions: tuple[Text, ...] = ()
    missing_conditions: tuple[Text, ...] = ()
    observed_concentration_percent: Percentage | None = None
    max_concentration_percent: Percentage | None = None


class IngredientScreeningResult(Contract):
    product_id: Identifier
    evidence_id: Identifier
    evidence_version: Text
    evidence_fingerprint: Text
    rule_set_id: Identifier
    rule_set_version: Text
    rule_set_fingerprint: Text
    findings: tuple[IngredientFinding, ...] = ()
    eligibility: Eligibility
    unresolved_reason_codes: tuple[ReasonCode, ...] = ()
