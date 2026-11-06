"""Node for adding an analysis plan to the running state."""

from collections.abc import Callable

from dataops_copilot.agent.models import PlanningContext
from dataops_copilot.agent.services.planner import Planner
from dataops_copilot.agent.state import InvestigationState

StateUpdate = dict[str, object]


def make_plan_analysis_node(planner: Planner) -> Callable[[InvestigationState], StateUpdate]:
    """Create a node that plans the next round of checks and counts the round."""

    def plan_analysis(state: InvestigationState) -> StateUpdate:
        """Plan read-only checks for the current investigation."""
        context = PlanningContext(
            request=state.request,
            historical_matches=state.historical_matches,
            prior_results=state.check_results,
            open_questions=state.assessment.open_questions if state.assessment else [],
        )
        return {
            "analysis_plan": planner(context),
            "iteration_count": state.iteration_count + 1,
        }

    return plan_analysis
