"""Tests for the RCA investigation-planning node."""

from dataops_copilot.agent.checks.models import CheckResult
from dataops_copilot.agent.models import AnalysisPlan, PlanningContext
from dataops_copilot.agent.nodes.planner import make_plan_analysis_node
from dataops_copilot.agent.state import InvestigationState
from tests.factories import make_assessment, make_plan, make_request


def test_plan_analysis_node_adds_plan_and_counts_iteration() -> None:
    """Store the plan returned by the injected planner and count the round."""
    request = make_request()
    expected_plan = make_plan()

    def fake_planner(context: PlanningContext) -> AnalysisPlan:
        assert context.request == request
        assert context.historical_matches == []
        assert context.prior_results == []
        assert context.open_questions == []
        return expected_plan

    node = make_plan_analysis_node(fake_planner)
    update = node(InvestigationState(request=request))

    assert update == {"analysis_plan": expected_plan, "iteration_count": 1}


def test_plan_analysis_node_passes_prior_results_and_open_questions() -> None:
    prior = CheckResult(check_name="value_range", params={}, metrics={}, succeeded=True)
    state = InvestigationState(
        request=make_request(),
        check_results=[prior],
        assessment=make_assessment(sufficient=False, open_questions=["Which vendor?"]),
        iteration_count=1,
    )
    seen: list[PlanningContext] = []

    def fake_planner(context: PlanningContext) -> AnalysisPlan:
        seen.append(context)
        return make_plan()

    update = make_plan_analysis_node(fake_planner)(state)

    assert seen[0].prior_results == [prior]
    assert seen[0].open_questions == ["Which vendor?"]
    assert update["iteration_count"] == 2
