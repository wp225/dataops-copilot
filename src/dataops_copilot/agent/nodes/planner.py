"""Node for adding an analysis plan to the running state."""

from collections.abc import Callable

from dataops_copilot.agent.models import AnalysisPlan
from dataops_copilot.agent.services.planner import Planner
from dataops_copilot.agent.state import InvestigationState


def make_plan_analysis_node(
    planner: Planner,
) -> Callable([InvestigationState], AnalysisPlan):
    """Create a node that adds an investigation plan to state."""

    def plan_analysis(state: InvestigationState) -> dict[str, AnalysisPlan]:
        """Plan read-only checks for the current investigation."""
        analysis_plan = planner(
            state.request,
            state.historical_matches,
        )
        return {"analysis_plan": analysis_plan}

    return plan_analysis
