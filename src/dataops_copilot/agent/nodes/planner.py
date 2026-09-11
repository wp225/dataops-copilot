"""Node for adding Analysis plan into the running state."""

from collections.abc import Callable

from dataops_copilot.agent.models import (
    AnalysisPlan,
    HistoricalIncidentMatch,
    IncidentInvestigationRequest,
)
from dataops_copilot.agent.state import InvestigationState

Planner = Callable[[IncidentInvestigationRequest, list[HistoricalIncidentMatch]], AnalysisPlan]


def make_plan_analysis_node(
    planner: Planner,
) -> Callable[[InvestigationState], dict[str, AnalysisPlan]]:
    """Create a node that adds investigation plan in state."""

    def plan_analysis(state: InvestigationState) -> dict[str, AnalysisPlan]:
        """Plan read-only checks for current investigation."""
        analysis_plan = planner(
            state.request,
            state.historical_matches,
        )

        return {"analysis_plan": analysis_plan}

    return plan_analysis
