"""Load one bounded, reviewed ingredient rule manifest without losing valid rules."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from schemas.ingredient_screening import IngredientRuleSet

RULE_MANIFEST_PATH = Path(__file__).resolve().parents[1] / "data/rules/india-limited-v1.json"
MAX_MANIFEST_BYTES = 256 * 1024

RuleManifestStatus = Literal["loaded", "retained_last_valid", "unavailable"]


@dataclass(frozen=True)
class RuleManifestOutcome:
    """Sanitized rule-load result; never include untrusted manifest content."""

    rules: IngredientRuleSet | None
    status: RuleManifestStatus
    message: str


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON member")
        value[key] = item
    return value


def _reject_constant(_: str) -> None:
    raise ValueError("Non-finite JSON value")


class RuleManifestStore:
    """Keep public, last-valid rules active when a replacement cannot be validated."""

    def __init__(self) -> None:
        self._rules: IngredientRuleSet | None = None

    def refresh(self, path: Path) -> RuleManifestOutcome:
        try:
            if not path.is_file():
                raise ValueError("Rule manifest is not a regular file")
            raw = path.read_bytes()
            if len(raw) > MAX_MANIFEST_BYTES:
                raise ValueError("Rule manifest exceeds size limit")
            decoded = json.loads(
                raw.decode("utf-8"),
                parse_constant=_reject_constant,
                object_pairs_hook=_unique_object,
            )
            rules = IngredientRuleSet.model_validate(decoded)
        except (OSError, UnicodeDecodeError, ValueError, ValidationError):
            if self._rules is not None:
                return RuleManifestOutcome(
                    rules=self._rules,
                    status="retained_last_valid",
                    message="Rule update was rejected; the last valid rule set remains active.",
                )
            return RuleManifestOutcome(
                rules=None,
                status="unavailable",
                message=(
                    "Reviewed ingredient rules are unavailable. "
                    "Try again after the rule file is restored."
                ),
            )
        self._rules = rules
        return RuleManifestOutcome(rules=rules, status="loaded", message="")
