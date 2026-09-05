"""Tests for the shared investigation state model."""

from dataops_copilot.agent.models import IncidentInvestigationRequest
from dataops_copilot.agent.state import InvestigationState
from dataops_copilot.quality.models import DataQualityIncident, QualityReport


def make_request() -> IncidentInvestigationRequest:
    """Create a small valid investigation request for testing."""
    return IncidentInvestigationRequest(
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


def test_investigation_state_defaults() -> None:
    """A freshly created state should carry only the request, with empty defaults."""
    state = InvestigationState(request=make_request())

    assert state.historical_matches == []
    assert state.current_plan is None
    assert state.generated_analysis is None
    assert state.code_validation is None
    assert state.analysis_result == []
    assert state.evidence_sufficient is False
    assert state.iteration_count == 0
    assert state.final_result is None
