from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_development_preview_starts_without_sources_models_or_catalog() -> None:
    page = AppTest.from_file(str(APP)).run()

    assert not page.exception
    assert not page.error
    assert page.title[0].value == "AI Cosmetic Product Advisor"
    assert "No catalog has been loaded" in page.info[0].value
    assert not page.button


def test_invalid_settings_show_redacted_error(monkeypatch: pytest.MonkeyPatch) -> None:
    value = "synthetic-sensitive-config-input"
    monkeypatch.setenv("ADVISOR_HOSTED_ENABLED", value)

    page = AppTest.from_file(str(APP)).run()

    assert not page.exception
    assert "Configuration is invalid" in page.error[0].value
    assert value not in page.error[0].value
    assert not page.info
