"""Synthetic request contracts for US-013 AC-1/AC-2; no real profiles."""

from decimal import Decimal, localcontext

import pytest
from pydantic import ValidationError

from schemas.requirements import UserRequirements


def request(**changes: object) -> UserRequirements:
    return UserRequirements.model_validate(
        {"category": "sunscreen", "skin_type": "oily", "budget_inr": "800", **changes}
    )


@pytest.mark.parametrize("category", ["sunscreen", "moisturiser"])
@pytest.mark.parametrize("skin_type", ["oily", "dry", "combination", "normal", "sensitive"])
def test_supported_requirements(category: str, skin_type: str) -> None:
    value = request(category=category, skin_type=skin_type)
    assert value.country == "India" and value.currency == "INR"
    assert value.budget_paise == 80_000
    assert value.exclusions == () and value.preferences is None


@pytest.mark.parametrize(
    ("budget", "paise"),
    [(0, 0), ("0.00", 0), ("800.01", 80_001), (Decimal("0.01"), 1), (800.01, 80_001)],
)
def test_exact_paise_without_rounding(budget: object, paise: int) -> None:
    assert request(budget_inr=budget).budget_paise == paise


@pytest.mark.parametrize(
    "budget",
    [
        None,
        "",
        " ",
        -1,
        "-0.01",
        "eight hundred",
        "NaN",
        "Infinity",
        float("nan"),
        float("inf"),
        True,
        False,
        "0.001",
        "800.009",
        [],
        {},
    ],
)
def test_invalid_budgets_fail_at_budget_field(budget: object) -> None:
    with pytest.raises(ValidationError) as caught:
        request(budget_inr=budget)
    assert caught.value.errors(include_input=False)[0]["loc"] == ("budget_inr",)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("category", "serum"),
        ("skin_type", "other"),
        ("country", "UK"),
        ("currency", "USD"),
        ("category", True),
    ],
)
def test_unsupported_values_are_not_coerced(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        request(**{field: value})


@pytest.mark.parametrize("field", ["category", "skin_type", "budget_inr"])
def test_required_fields_cannot_be_omitted(field: str) -> None:
    values = {"category": "sunscreen", "skin_type": "oily", "budget_inr": "800"}
    values.pop(field)
    with pytest.raises(ValidationError):
        UserRequirements.model_validate(values)


def test_optional_preferences_and_exclusions_remain_in_memory_and_out_of_repr() -> None:
    sentinel = "synthetic-private-exclusion"
    value = request(exclusions=[sentinel], preferences={"texture": "gel", "finish": "matte"})
    assert value.exclusions == (sentinel,)
    assert value.preferences is not None and value.preferences.finish == "matte"
    assert sentinel not in repr(value)
    assert "800" not in repr(value)
    # Explicit serialization is for in-memory use only; there is no persistence API here.
    assert UserRequirements.model_validate_json(value.model_dump_json()) == value
    with pytest.raises(ValidationError):
        value.budget_inr = Decimal("10")


def test_validation_diagnostics_hide_rejected_input() -> None:
    sentinel = "synthetic-sensitive-budget"
    with pytest.raises(ValidationError) as caught:
        request(budget_inr=sentinel)
    assert sentinel not in str(caught.value)
    assert "budget_inr" in str(caught.value)


@pytest.mark.parametrize(
    "changes",
    [
        {"exclusions": [""]},
        {"preferences": {"finish": " "}},
        {"preferences": {"unknown": "x"}},
        {"budget_paise": 1},
    ],
)
def test_blank_or_undeclared_optional_inputs_are_rejected(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        request(**changes)


def test_public_error_messages_omit_private_values_and_unknown_field_names() -> None:
    sentinel = "synthetic-private-unknown-key"
    with pytest.raises(ValidationError) as caught:
        request(**{"budget_inr": "synthetic-private-budget", sentinel: "private-value"})
    messages = UserRequirements.validation_messages(caught.value)
    assert any("budget_inr" in message for message in messages)
    assert all(
        "synthetic-private" not in message and "private-value" not in message
        for message in messages
    )


def test_budget_conversion_does_not_round_under_a_small_decimal_context() -> None:
    with localcontext() as context:
        context.prec = 2
        assert request(budget_inr="800.01").budget_paise == 80_001
