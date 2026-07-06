"""Application configuration."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """FederalSpendAI runtime settings."""

    model_config = SettingsConfigDict(env_prefix="FEDERALSPEND_", env_file=".env", extra="ignore")

    data_dir: Path = Field(default_factory=lambda: Path.home() / ".federalspendai")
    db_path: Path | None = None
    lang: str = "en"
    ckan_base_url: str = "https://open.canada.ca/data/en/api/3/action"
    request_timeout: float = 60.0
    default_limit: int = 50
    max_limit: int = 500

    @property
    def database_path(self) -> Path:
        if self.db_path is not None:
            return self.db_path
        return self.data_dir / "data.duckdb"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"


def get_settings() -> Settings:
    return Settings()
