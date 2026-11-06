"""Models for data-quality root-cause investigations."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from dataops_copilot.agent.checks.models import CheckResult, PlannedCheck
from dataops_copilot.quality.models import DataQualityIncident, QualityReport

type Confidence = Literal["low", "medium", "high"]


class IncidentInvestigationRequest(BaseModel):
    """Provide evidence needed to investigate one incident."""

    incident: DataQualityIncident
    quality_report: QualityReport
    dataset_name: str
    batch_id: str
    data_uri: str | None = Field(
        default=None,
        description="Parquet location of the batch (local path, abfss:// or https:// URI).",
    )
    requested_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RCAReport(BaseModel):
    """Record an evidence-backed, advisory RCA assessment."""

    likely_cause: str
    confidence: Confidence
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


class HistoricalIncidentMatch(BaseModel):
    """Historic Similar Incident."""

    historical_incident: IncidentRCAReport
    similarity_reasons: list[str]


class AnalysisHypothesis(BaseModel):
    """Describe one plausible hypothesis for incident."""

    likely_cause: str
    rationale: str
    likelihood: Confidence
    checks_to_run: list[PlannedCheck] = Field(min_length=1)


class AnalysisPlan(BaseModel):
    """Analysis plan for a hypothesis."""

    hypotheses: list[AnalysisHypothesis] = Field(min_length=1, max_length=3)
    analysis_goal: str

    def planned_checks(self) -> list[PlannedCheck]:
        """Return every check in the plan, de-duplicated, in plan order."""
        seen: set[tuple[str, str | None, str | None, str | None]] = set()
        checks: list[PlannedCheck] = []
        for hypothesis in self.hypotheses:
            for check in hypothesis.checks_to_run:
                if check.key() not in seen:
                    seen.add(check.key())
                    checks.append(check)
        return checks


class PlanningContext(BaseModel):
    """Everything the planner sees when it plans the next round of checks."""

    request: IncidentInvestigationRequest
    historical_matches: list[HistoricalIncidentMatch] = Field(default_factory=list)
    prior_results: list[CheckResult] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class EvidenceAssessment(BaseModel):
    """Judgement on whether the evidence gathered so far explains the incident."""

    evidence_sufficient: bool = Field(
        description="True only if the check results directly support one root cause."
    )
    supported_cause: str | None = Field(
        default=None, description="The cause the evidence supports, if any."
    )
    confidence: Confidence
    reasoning: str = Field(description="How the check results support or fail to support it.")
    open_questions: list[str] = Field(
        default_factory=list,
        description="What is still unknown and which evidence would resolve it.",
    )


class InvestigationContext(BaseModel):
    """Evidence handed to the assessor and the report writer."""

    request: IncidentInvestigationRequest
    historical_matches: list[HistoricalIncidentMatch] = Field(default_factory=list)
    analysis_plan: AnalysisPlan | None = None
    check_results: list[CheckResult] = Field(default_factory=list)
    assessment: EvidenceAssessment | None = None
