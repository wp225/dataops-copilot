"""Data Modeling for Investigation."""

from pydantic import BaseModel, ConfigDict


class CheckResult(BaseModel):
    """Base model for investigation checks."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    check_name: str
    params: dict[str, str]
    metrics: dict[str, float]
    succeeded: bool
    error: str | None = None
