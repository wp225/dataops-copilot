"""Tests for evidence assessment, routing and report writing."""

from dataops_copilot.agent.checks.models import CheckResult
from dataops_copilot.agent.models import EvidenceAssessment, InvestigationContext, RCAReport
from dataops_copilot.agent.nodes.assess import make_assess_evidence_node, make_assessment_router
from dataops_copilot.agent.nodes.report import make_write_report_node
from dataops_copilot.agent.state import InvestigationState
from tests.factories import (
    make_assessment,
    make_completed_investigation,
    make_rca_report,
    make_request,
)


def test_assess_node_stores_assessment() -> None:
    expected = make_assessment(sufficient=True)

    request = make_request()

    def fake_assessor(context: InvestigationContext) -> EvidenceAssessment:
        assert context.request == request
        return expected

    update = make_assess_evidence_node(fake_assessor)(InvestigationState(request=request))

    assert update == {"assessment": expected}


def test_router_loops_until_sufficient_or_capped() -> None:
    route = make_assessment_router(max_iterations=2)
    base = InvestigationState(request=make_request())

    insufficient = make_assessment(sufficient=False)
    assert route(base.model_copy(update={"assessment": insufficient, "iteration_count": 1})) == (
        "analysis_planning"
    )
    assert route(base.model_copy(update={"assessment": insufficient, "iteration_count": 2})) == (
        "write_report"
    )
    sufficient = make_assessment(sufficient=True)
    assert route(base.model_copy(update={"assessment": sufficient, "iteration_count": 1})) == (
        "write_report"
    )


def _state(*, sufficient: bool) -> InvestigationState:
    return InvestigationState(
        request=make_request(),
        historical_matches=[],
        check_results=[
            CheckResult(
                check_name="value_range",
                params={"column": "fare_amount"},
                metrics={"min": -5.0},
                succeeded=True,
            ),
            CheckResult(
                check_name="value_range",
                params={"column": "nope"},
                metrics={},
                succeeded=False,
                error="Column 'nope' does not exist.",
            ),
        ],
        assessment=make_assessment(sufficient=sufficient),
    )


def test_report_node_sets_factual_fields_from_state() -> None:
    def fake_writer(_: InvestigationContext) -> RCAReport:
        return make_rca_report(
            confidence="high", previous_similar_incidents=99, analyses_executed=["made up"]
        )

    state = _state(sufficient=True)
    update = make_write_report_node(fake_writer)(state)
    final = update["final_result"]

    assert final.request == state.request
    assert final.report.previous_similar_incidents == 0
    assert final.report.analyses_executed == ["value_range(column=fare_amount)"]
    assert final.report.confidence == "high"
    assert final.report.escalation_required is False


def test_report_node_escalates_when_evidence_insufficient() -> None:
    def fake_writer(_: InvestigationContext) -> RCAReport:
        return make_rca_report(confidence="high", escalation_required=False)

    final = make_write_report_node(fake_writer)(_state(sufficient=False))["final_result"]

    assert final.report.escalation_required is True
    assert final.report.confidence == "low"


def test_history_count_comes_from_matches() -> None:
    from dataops_copilot.agent.models import HistoricalIncidentMatch

    state = _state(sufficient=True).model_copy(
        update={
            "historical_matches": [
                HistoricalIncidentMatch(
                    historical_incident=make_completed_investigation(), similarity_reasons=["x"]
                )
            ]
        }
    )

    final = make_write_report_node(lambda _: make_rca_report())(state)["final_result"]

    assert final.report.previous_similar_incidents == 1
