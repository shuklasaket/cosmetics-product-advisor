"""Validated local configuration with no side effects or secret diagnostics."""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Foundation settings; future capabilities extend this explicit contract."""

    model_config = SettingsConfigDict(
        env_prefix="ADVISOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    data_dir: Path = Path("data/local")
    database_path: Path = Path("database/advisor.db")
    export_dir: Path = Path("exports")
    hosted_enabled: bool = False

    @field_validator("data_dir", "database_path", "export_dir", mode="before")
    @classmethod
    def reject_blank_path(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            raise ValueError("Configure a non-empty local path.")
        return value

    @field_validator("hosted_enabled")
    @classmethod
    def require_local_inference(cls, enabled: bool) -> bool:
        if enabled:
            raise ValueError("Hosted inference is not implemented in the development foundation.")
        return enabled
