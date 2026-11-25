"""Typed, synthetic-first ingredient-screening contracts for PRD 03."""

from datetime import date
from typing import Literal

from pydantic import Field, field_validator, model_validator

from schemas.catalog import Reference
from schemas.common import Category, Contract, Identifier, Text

RuleType = Literal["prohibited", "restricted"]
FindingStatus = Literal["prohibited", "restricted_satisfied", "requires_verification"]
Eligibility = Literal["eligible_within_checks", "excluded", "requires_verification"]


def _normalized(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


class IngredientRule(Contract):
    rule_id: Identifier
    canonical_ingredient: Text
    aliases: tuple[Text, ...] = ()
    rule_type: RuleType
    categories: tuple[Category, ...] = ()
    required_conditions: tuple[Text, ...] = ()
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
        if self.rule_type == "prohibited" and self.required_conditions:
            raise ValueError("Prohibited rules cannot require conditions.")
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
    declaration: Text | None = None
    completeness: Literal["complete", "partial", "unknown"]
    conditions: tuple[Text, ...] = ()


class IngredientFinding(Contract):
    rule_id: Identifier
    canonical_ingredient: Text
    matched_declaration: Text
    status: FindingStatus
    source_reference: Reference
    source_section: Text
    missing_conditions: tuple[Text, ...] = ()


class IngredientScreeningResult(Contract):
    product_id: Identifier
    evidence_id: Identifier
    evidence_version: Text
    rule_set_id: Identifier
    rule_set_version: Text
    findings: tuple[IngredientFinding, ...] = ()
    eligibility: Eligibility
    unresolved_reason_codes: tuple[Literal["incomplete_ingredient_evidence"], ...] = ()
