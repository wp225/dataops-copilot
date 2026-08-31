"""Models for data-quality root-cause investigations."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from dataops_copilot.quality.models import DataQualityIncident, QualityReport


class IncidentInvestigationRequest(BaseModel):
    """Provide evidence needed to investigate one incident."""

    incident: DataQualityIncident
    quality_report: QualityReport
    dataset_name: str
    batch_id: str
    requested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RCAReport(BaseModel):
    """Record an evidence-backed, advisory RCA assessment."""

    likely_cause: str
    confidence: Literal["low", "medium", "high"]
    explanation: str
    previous_similar_incidents: int
    evidence: list[str]
    analyses_executed: list[str]
    escalation_required: bool
    recommendations: list[str]


class IncidentRCAReport(BaseModel):
    """Preserve the request and its completed RCA report."""

    request: IncidentInvestigationRequest
    report: RCAReport
    completed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

