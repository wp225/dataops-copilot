"""Data Modeling for Spark Quality Profiling."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

type Rate = Annotated[float, Field(ge=0.0, le=1.0)]


class QualityReport(BaseModel):
    """Deterministic Quality Metrices."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    row_count: Annotated[int, Field(ge=0)]
    null_rates: dict[str, Rate]
    duplicate_rate: Rate
    negative_fare_rate: Rate
    invalid_trip_distance_rate: Rate

class DataQualityIncident(BaseModel):
    """Describes data quality violation."""

    metric: str
    observed_rate: Rate
    threshold: Rate
    affected_column: str | None = None
