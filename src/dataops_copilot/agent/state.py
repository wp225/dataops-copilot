"""Shared State Space for Investigation Run."""
from typing import NotRequired, TypedDict
from pydantic import BaseModel, Field

from dataops_copilot.agent.models import (
    AnalysisExecutionResult,
    AnalysisPlan,
    CodeValidationResult,
    GeneratedAnalysis,
    HistoricalIncidentMatch,
    IncidentInvestigationRequest,
    IncidentRCAReport,
)

class InvestigationState(BaseModel):
    """Track Evidence and descisions for investigation runs."""
    
    request: IncidentInvestigationRequest
    
    historical_matches: list[HistoricalIncidentMatch] = Field(default_factory=list)
    current_plan: AnalysisPlan | None = None
    generated_analysis: GeneratedAnalysis | None = None
    code_validation: CodeValidationResult | None = None
    analysis_result: list[AnalysisExecutionResult] = Field(default_factory=list)
    
    evidence_sufficient: bool = False
    iteration_count: int = 0
    final_result: IncidentRCAReport | None = None