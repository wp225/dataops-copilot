"""Shared State Space for Investigation Run."""

from pydantic import BaseModel, Field

from dataops_copilot.agent.checks.models import CheckResult
from dataops_copilot.agent.models import (
    AnalysisPlan,
    EvidenceAssessment,
    HistoricalIncidentMatch,
    IncidentInvestigationRequest,
    IncidentRCAReport,
    InvestigationContext,
)


class InvestigationState(BaseModel):
    """Track Evidence and decisions for investigation runs."""

    request: IncidentInvestigationRequest

    historical_matches: list[HistoricalIncidentMatch] = Field(default_factory=list)
    analysis_plan: AnalysisPlan | None = None
    check_results: list[CheckResult] = Field(default_factory=list)
    assessment: EvidenceAssessment | None = None

    iteration_count: int = 0
    final_result: IncidentRCAReport | None = None

    @property
    def evidence_sufficient(self) -> bool:
        """Whether the latest assessment found the evidence sufficient."""
        return self.assessment is not None and self.assessment.evidence_sufficient

    def to_context(self) -> InvestigationContext:
        """Return the evidence an LLM step needs, without loop bookkeeping."""
        return InvestigationContext(
            request=self.request,
            historical_matches=self.historical_matches,
            analysis_plan=self.analysis_plan,
            check_results=self.check_results,
            assessment=self.assessment,
        )
