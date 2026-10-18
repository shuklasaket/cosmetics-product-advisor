"""Shared primitives for the catalog-v1 boundary contracts."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, ValidationError

Category = Literal["sunscreen", "moisturiser"]
SkinType = Literal["oily", "dry", "combination", "normal", "sensitive"]
Text = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]
Identifier = Annotated[
    str, StringConstraints(strict=True, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
]


class Contract(BaseModel):
    """Reject undeclared fields and keep validated values immutable."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @classmethod
    def validation_messages(cls, error: ValidationError) -> tuple[str, ...]:
        """Public diagnostics contain declared field names and fixed text only.

        Even errors(include_input=False) can contain private extra-field names or
        exception context. Never expose/serialize a raw ValidationError instead.
        """
        hints = {
            "budget_inr": "Enter a finite non-negative INR maximum in whole paise.",
            "category": "Choose sunscreen or moisturiser.",
            "skin_type": "Choose oily, dry, combination, normal or sensitive.",
            "country": "Choose India.",
            "currency": "Choose INR.",
        }
        messages = []
        for detail in error.errors(include_input=False, include_context=False, include_url=False):
            first = detail["loc"][0] if detail["loc"] else None
            field = first if isinstance(first, str) and first in cls.model_fields else "record"
            if detail["type"] == "extra_forbidden":
                hint = "Remove unsupported fields."
            elif detail["type"] == "missing":
                hint = "Supply the required field."
            else:
                hint = hints.get(
                    field,
                    "Check supported types/ranges, identity, source evidence and resolution links.",
                )
            messages.append(f"{field}: {hint}")
        return tuple(messages)
