from pathlib import Path

import pytest
from pydantic import ValidationError
from streamlit.testing.v1 import AppTest
from test_catalog_contracts import catalog
from test_catalog_search import product

from repositories.catalog import CatalogRepository, migrate
from schemas.catalog import CatalogEnvelope
from schemas.requirements import UserRequirements
from ui.catalog_results import safe_https_reference
from ui.search_form import build_search_request

APP = Path(__file__).resolve().parents[1] / "app.py"


def store_app_catalog(*products: dict) -> None:
    data = catalog()
    for table in ("products", "observations", "resolutions"):
        data[table] = [item for part in products for item in part[table]]
    path = Path("database/advisor.db")
    migrate(path)
    CatalogRepository(path).save(CatalogEnvelope.model_validate(data))


def submit_default_search(page: AppTest, *, budget: str = "800") -> AppTest:
    page.text_input(key="search_budget").set_value(budget)
    return page.form_submit_button[0].click().run()


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


def test_search_renders_ordered_entries_and_inspectable_detail_evidence() -> None:
    store_app_catalog(
        product("beta", name="Beta"),
        product("alpha-z", name="Alpha"),
        product("alpha-a", name="Alpha"),
    )
    page = submit_default_search(AppTest.from_file(str(APP)).run())

    assert not page.exception
    result_names = [item.value for item in page.text if item.value in {"Alpha", "Beta"}]
    assert result_names == ["Alpha", "Alpha", "Beta"]
    assert [
        page.button(key=key).label for key in ("detail_alpha-a", "detail_alpha-z", "detail_beta")
    ] == ["View details", "View details", "View details"]
    assert not any("suitability score" in item.value.lower() for item in page.markdown)

    page.button(key="detail_alpha-a").click().run()

    assert not page.exception
    assert page.subheader[-1].value == "Product details"
    detail_text = [item.value for item in page.text]
    assert "Alpha" in detail_text
    assert "₹800.00" in detail_text
    assert "Synthetic A, B" in detail_text
    assert "2026-10-19T10:00:00Z" in detail_text
    assert "Synthetic fixture" in detail_text
    detail_links = [item.url for item in page.link_button]
    assert "https://example.test/facts" in detail_links


def test_detail_labels_unknown_sponsorship_and_declared_claims_honestly() -> None:
    item = product(
        "unknowns",
        skin_type_claims=["oily", "sensitive"],
        review_count=None,
        sponsorship="unknown",
    )
    item["products"][0]["pack_size"] = None
    next(o for o in item["observations"] if o["field_name"] == "pack_size")["value"] = None
    store_app_catalog(item)
    page = submit_default_search(AppTest.from_file(str(APP)).run())
    page.button(key="detail_unknowns").click().run()

    assert not page.exception
    labels = [item.value for item in page.caption]
    values = [item.value for item in page.text]
    assert "Pack size" in labels and "Unknown" in values
    assert "Sponsorship" in labels and "Unknown (evidence-backed)" in values
    assert "Declared skin-type claims" in labels
    assert "oily, sensitive" in values
    assert any("not a safety or suitability finding" in item.value for item in page.info)


def test_empty_result_explains_active_filters_and_allows_retry() -> None:
    store_app_catalog(product("over-budget", price_paise=80_001))
    page = submit_default_search(AppTest.from_file(str(APP)).run())

    assert not page.exception
    assert "detail_over-budget" not in {button.key for button in page.button}
    empty_message = " ".join(item.value for item in page.info)
    assert "sunscreen" in empty_message
    assert "India" in empty_message
    assert "₹800.00" in empty_message
    assert "Change the filters" in empty_message

    page.text_input(key="search_budget").set_value("800.01")
    page.form_submit_button[0].click().run()

    assert page.button(key="detail_over-budget").label == "View details"
    assert not page.error


def test_unavailable_catalog_clears_results_and_recovers_after_restore() -> None:
    page = submit_default_search(AppTest.from_file(str(APP)).run())

    assert not page.exception
    assert "Catalog unavailable or invalid" in page.error[0].value
    assert "restore a verified backup" in page.error[0].value
    assert "database/advisor.db" not in page.error[0].value
    assert "active_search_result" not in page.session_state

    store_app_catalog(product("restored"))
    page.form_submit_button[0].click().run()

    assert not page.error
    assert page.button(key="detail_restored").label == "View details"


def test_external_text_is_inert_and_unsafe_references_are_not_links() -> None:
    script_like = '<script>alert("synthetic")</script>'
    store_app_catalog(product("hostile", ingredient_declaration=script_like))
    page = submit_default_search(AppTest.from_file(str(APP)).run())
    page.button(key="detail_hostile").click().run()

    assert script_like in [item.value for item in page.text]
    assert not page.html
    assert script_like not in " ".join(item.value for item in page.markdown)
    assert safe_https_reference("javascript:alert(1)") is None
    assert safe_https_reference("data:text/html,unsafe") is None
    assert safe_https_reference("document:local-evidence") is None
    assert safe_https_reference("https://example.test/fact") == "https://example.test/fact"
