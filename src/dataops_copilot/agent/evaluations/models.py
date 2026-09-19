"""Models for planner evaluation cases."""

from pydantic import BaseModel, Field

from dataops_copilot.agent.models import (
    HistoricalIncidentMatch,
    IncidentInvestigationRequest,
)


class PlannerEvaluationCase(BaseModel):
    """Define one golden evaluation case for the RCA planner."""

    case_id: str
    request: IncidentInvestigationRequest
    historical_matches: list[HistoricalIncidentMatch] = Field(default_factory=list)
    expected_cause_categories: list[str] = Field(min_length=1)
    required_checks: list[str] = Field(min_length=1)
    escalation_expected: bool
