"""Tests for the RCA investigation-planning node."""

from dataops_copilot.agent.models import (
    AnalysisHypothesis,
    AnalysisPlan,
    IncidentInvestigationRequest,
)
from dataops_copilot.agent.nodes.planner import make_plan_analysis_node
from dataops_copilot.agent.state import InvestigationState
from dataops_copilot.quality.models import DataQualityIncident, QualityReport


def test_plan_analysis_node_adds_planner_result_to_state() -> None:
    """Store the plan returned by the injected planner."""
    request = IncidentInvestigationRequest(
        incident=DataQualityIncident(
            metric="negative_fare_rate",
            observed_rate=0.01,
            threshold=0.001,
            affected_column="fare_amount",
        ),
        quality_report=QualityReport(
            row_count=100,
            negative_fare_rate=0.01,
            invalid_trip_distance_rate=0.0,
            duplicate_rate=0.0,
            null_rates={"fare_amount": 0.0},
        ),
        dataset_name="yellow-taxi",
        batch_id="batch-001",
    )
    expected_plan = AnalysisPlan(
        analysis_goal="Identify the source of negative fares.",
        hypotheses=[
            AnalysisHypothesis(
                likely_cause="Refund values were mapped into fare_amount.",
                rationale="The negative-fare rate exceeds the policy threshold.",
                likelihood="medium",
                checks_to_run=["Compare negative fares by payment type."],
            )
        ],
    )

    def fake_planner(
        received_request: IncidentInvestigationRequest,
        historical_matches: list[object],
    ) -> AnalysisPlan:
        assert received_request == request
        assert historical_matches == []
        return expected_plan

    node = make_plan_analysis_node(fake_planner)
    update = node(InvestigationState(request=request))

    assert update == {"analysis_plan": expected_plan}
