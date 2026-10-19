from pathlib import Path

import pytest
from pydantic import ValidationError
from streamlit.testing.v1 import AppTest

from schemas.requirements import UserRequirements
from ui.search_form import build_search_request

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_search_form_shows_supported_choices_and_private_input_disclosure() -> None:
    page = AppTest.from_file(str(APP)).run()

    assert not page.exception
    assert not page.error
    assert page.title[0].value == "AI Cosmetic Product Advisor"
    assert page.segmented_control(key="search_category").options == [
        "Sunscreen",
        "Moisturiser",
    ]
    assert page.selectbox(key="search_skin_type").options == [
        "Oily",
        "Dry",
        "Combination",
        "Normal",
        "Sensitive",
    ]
    assert page.text_input(key="search_country").value == "India"
    assert page.text_input(key="search_currency").value == "INR"
    assert "only in this browser session" in page.caption[1].value


def test_valid_zero_budget_dispatches_validated_requirements() -> None:
    page = AppTest.from_file(str(APP)).run()

    page.segmented_control(key="search_category").set_value("Moisturiser")
    page.selectbox(key="search_skin_type").set_value("Sensitive")
    page.text_input(key="search_budget").set_value("0")
    page.form_submit_button[0].click().run()

    request = page.session_state["active_search_request"]
    assert isinstance(request, UserRequirements)
    assert request.category == "moisturiser"
    assert request.skin_type == "sensitive"
    assert request.budget_paise == 0
    assert request.exclusions == ()
    assert request.preferences is None
    assert page.session_state["search_dispatch_count"] == 1
    assert "validated" in page.success[0].value.lower()


@pytest.mark.parametrize(
    ("field", "value"),
    [("category_label", "Serum"), ("skin_type_label", "Other")],
)
def test_unsupported_choice_at_ui_boundary_is_rejected(field: str, value: str) -> None:
    values = {
        "category_label": "Sunscreen",
        "skin_type_label": "Oily",
        "budget": "800",
        "exclusions": "",
        "texture": "",
        "finish": "",
    }
    values[field] = value

    with pytest.raises(ValidationError) as caught:
        build_search_request(**values)

    messages = UserRequirements.validation_messages(caught.value)
    assert any("Choose" in message for message in messages)
    assert value not in " ".join(messages)


@pytest.mark.parametrize("budget", ["", "-0.01", "eight hundred", "NaN", "Infinity"])
def test_invalid_budget_blocks_dispatch_and_corrected_resubmit_succeeds(budget: str) -> None:
    page = AppTest.from_file(str(APP)).run()

    page.text_input(key="search_budget").set_value(budget)
    page.form_submit_button[0].click().run()

    assert "active_search_request" not in page.session_state
    assert page.session_state.get("search_dispatch_count", 0) == 0
    assert any("finite non-negative INR maximum" in error.value for error in page.error)

    page.text_input(key="search_budget").set_value("800.01")
    page.form_submit_button[0].click().run()

    assert page.session_state["active_search_request"].budget_paise == 80_001
    assert page.session_state["search_dispatch_count"] == 1


def test_private_inputs_clear_without_persistence_or_query_parameters(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    sentinel = "synthetic-private-ingredient"
    page = AppTest.from_file(str(APP)).run()
    page.text_input(key="search_budget").set_value("450")
    page.text_area(key="search_exclusions").set_value(sentinel)
    page.text_input(key="search_texture").set_value("gel")
    page.text_input(key="search_finish").set_value("matte")
    page.form_submit_button[0].click().run()

    request = page.session_state["active_search_request"]
    assert request.exclusions == (sentinel,)
    assert request.preferences is not None and request.preferences.finish == "matte"
    assert not dict(page.query_params)
    assert not list(tmp_path.rglob("*.sqlite*"))
    assert sentinel not in caplog.text
    assert sentinel not in capsys.readouterr().out

    page.button(key="clear_search").click().run()

    assert page.text_input(key="search_budget").value == ""
    assert page.text_area(key="search_exclusions").value == ""
    assert page.text_input(key="search_texture").value == ""
    assert page.text_input(key="search_finish").value == ""
    assert "active_search_request" not in page.session_state
    assert "search_dispatch_count" not in page.session_state

    fresh_page = AppTest.from_file(str(APP)).run()
    assert fresh_page.text_area(key="search_exclusions").value == ""
    assert "active_search_request" not in fresh_page.session_state


def test_invalid_settings_show_redacted_error(monkeypatch: pytest.MonkeyPatch) -> None:
    value = "synthetic-sensitive-config-input"
    monkeypatch.setenv("ADVISOR_HOSTED_ENABLED", value)

    page = AppTest.from_file(str(APP)).run()

    assert not page.exception
    assert "Configuration is invalid" in page.error[0].value
    assert value not in page.error[0].value
    assert not page.info
