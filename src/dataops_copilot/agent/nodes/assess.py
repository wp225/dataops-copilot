"""Node that judges whether the gathered evidence explains the incident."""

from collections.abc import Callable
from typing import Literal

from dataops_copilot.agent.services.assessor import Assessor
from dataops_copilot.agent.state import InvestigationState

StateUpdate = dict[str, object]
NextStep = Literal["analysis_planning", "write_report"]


def make_assess_evidence_node(assessor: Assessor) -> Callable[[InvestigationState], StateUpdate]:
    """Create a node that stores the assessor's judgement in state."""

    def assess_evidence(state: InvestigationState) -> StateUpdate:
        return {"assessment": assessor(state.to_context())}

    return assess_evidence


def make_assessment_router(max_iterations: int) -> Callable[[InvestigationState], NextStep]:
    """Route back to planning until evidence is sufficient or the round cap is hit."""

    def route(state: InvestigationState) -> NextStep:
        if state.evidence_sufficient or state.iteration_count >= max_iterations:
            return "write_report"
        return "analysis_planning"

    return route
