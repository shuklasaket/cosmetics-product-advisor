"""Session-only shopper input; never use as a persistence or logging record."""

from decimal import Decimal, InvalidOperation
from typing import Literal

from pydantic import Field, field_validator

from schemas.common import Category, Contract, SkinType, Text


class Preferences(Contract):
    texture: Text | None = Field(default=None, repr=False)
    finish: Text | None = Field(default=None, repr=False)


class UserRequirements(Contract):
    category: Category = Field(repr=False)
    skin_type: SkinType = Field(repr=False)
    country: Literal["India"] = Field(default="India", repr=False)
    currency: Literal["INR"] = Field(default="INR", repr=False)
    budget_inr: Decimal = Field(repr=False)
    exclusions: tuple[Text, ...] = Field(default=(), repr=False)
    preferences: Preferences | None = Field(default=None, repr=False)

    @field_validator("budget_inr", mode="before")
    @classmethod
    def validate_budget(cls, value: object) -> Decimal:
        message = "Enter a finite non-negative INR maximum in whole paise (at most two decimals)."
        if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
            raise ValueError(message)
        try:
            amount = Decimal(str(value))
        except InvalidOperation:
            raise ValueError(message) from None
        if not amount.is_finite() or amount < 0:
            raise ValueError(message)
        numerator, denominator = amount.as_integer_ratio()
        if (numerator * 100) % denominator:
            raise ValueError(message)
        return amount

    @property
    def budget_paise(self) -> int:
        """Exact integer conversion independent of the ambient Decimal context."""
        numerator, denominator = self.budget_inr.as_integer_ratio()
        return numerator * 100 // denominator
