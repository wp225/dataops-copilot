"""Runtime configuration, read from DATAOPS_* environment variables or .env."""

import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

from dataops_copilot.agent.services.llm import DEFAULT_MODEL, Effort


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_prefix="DATAOPS_", env_file=".env", extra="ignore")

    anthropic_model: str = DEFAULT_MODEL
    anthropic_effort: Effort = "medium"
    max_iterations: int = 3
    quality_threshold_rate: float = 0.001

    report_store: Literal["local", "adls"] = "local"
    local_report_path: Path = Path("data/rca_reports.json")
    adls_account_url: str | None = None
    adls_container: str = "dataops"

    data_cache_dir: Path = Path(tempfile.gettempdir()) / "dataops-copilot"
    spark_app_name: str = "dataops-copilot"


@lru_cache
def get_settings() -> Settings:
    """Return process-wide settings.

    Also exports .env into the process environment, so the Anthropic and
    LangSmith clients see ANTHROPIC_API_KEY and LANGSMITH_* when run locally.
    Variables already set in the environment win.
    """
    load_dotenv(override=False)
    return Settings()
