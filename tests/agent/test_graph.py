"""Integration test for RCA LangGraph workflow."""

from pathlib import Path

from dataops_copilot.agent.graph import build_investigation_graph
from dataops_copilot.agent.models import (
    DataQualityIncident,
    IncidentInvestigationRequest,
    QualityReport,
)


def test_graph_adds_empty_historical_matches_when_no_case_exist(tmp_path: Path) -> None:
    """Run the graph and verify that the history node updates state."""
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
        dataset_name="yellow_taxi",
        batch_id="batch__001",
    )

    rca_dump_path = tmp_path / "rca_reports.json"
    rca_dump_path.write_text("[]", encoding="utf-8")

    graph = build_investigation_graph(rca_dump_path)
    result = graph.invoke({"request": request})
    assert result["historical_matches"] == []
