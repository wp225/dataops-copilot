"""Tests for the search-history langgraph node."""

import json
from pathlib import Path

from dataops_copilot.agent.models import (
    IncidentInvestigationRequest,
    IncidentRCAReport,
    RCAReport,
)
from dataops_copilot.agent.nodes.history import make_search_history_node
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


def make_completed_investigation() -> IncidentRCAReport:
    """Create a past RCA record for testing."""
    return IncidentRCAReport(
        request=make_request(),
        report=RCAReport(
            likely_cause="Test cause",
            confidence="medium",
            explanation="Test explanation",
            previous_similar_incidents=0,
            evidence=["Test evidence"],
            analyses_executed=["Test analysis"],
            escalation_required=False,
            recommendations=["Test recommendation"],
        ),
    )


def test_search_history_node_returns_historic_matches(tmp_path: Path) -> None:
    """The node should surface matches found by search_rca_reports as node output."""
    dump_path = tmp_path / "rca_reports.json"
    dump_path.write_text(
        json.dumps([make_completed_investigation().model_dump(mode="json")]),
        encoding="utf-8",
    )

    search_history = make_search_history_node(dump_path)
    state = InvestigationState(request=make_request())

    result = search_history(state)

    assert len(result["historic_matches"]) == 1
    assert result["historic_matches"][0].historical_incident.request.incident.metric == (
        "negative_fare_rate"
    )
