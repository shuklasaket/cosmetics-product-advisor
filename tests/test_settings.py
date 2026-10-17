from pathlib import Path

import pytest
from pydantic import ValidationError

from schemas.settings import Settings


def test_defaults_do_not_create_runtime_data(tmp_path: Path) -> None:
    settings = Settings()

    assert settings.hosted_enabled is False
    assert not (tmp_path / settings.database_path).exists()
    assert not (tmp_path / settings.data_dir).exists()
    assert not (tmp_path / settings.export_dir).exists()


def test_environment_overrides_dotenv_without_exposing_values(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / ".env").write_text("ADVISOR_DATA_DIR=data/from-file\n", encoding="utf-8")
    monkeypatch.setenv("ADVISOR_DATA_DIR", "data/from-environment")

    assert Settings().data_dir == Path("data/from-environment")


@pytest.mark.parametrize("value", ["true", "1", "on"])
def test_hosted_inference_cannot_be_activated(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("ADVISOR_HOSTED_ENABLED", value)

    with pytest.raises(ValidationError, match="not implemented"):
        Settings()


def test_invalid_configuration_does_not_echo_input(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "synthetic-sensitive-value-for-test"
    monkeypatch.setenv("ADVISOR_HOSTED_ENABLED", secret)

    with pytest.raises(ValidationError) as error:
        Settings()

    assert secret not in str(error.value)


@pytest.mark.parametrize("field", ["DATA_DIR", "DATABASE_PATH", "EXPORT_DIR"])
def test_blank_paths_are_rejected(monkeypatch: pytest.MonkeyPatch, field: str) -> None:
    monkeypatch.setenv(f"ADVISOR_{field}", "   ")

    with pytest.raises(ValidationError, match="non-empty local path"):
        Settings()


def test_unknown_dotenv_setting_is_rejected(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("ADVISOR_MISSPELLED_OPTION=false\n", encoding="utf-8")

    with pytest.raises(ValidationError, match="Extra inputs"):
        Settings()
