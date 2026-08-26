from pydantic import BaseModel, ConfigDict


class QualityPolicy(BaseModel):
    """Deterministic data-quality rate."""
    model_config = ConfigDict(frozen=True, extra="forbid")
    threshold_rate: float = 0.001
