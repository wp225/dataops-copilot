"""Tests for historical RCA retrieval."""

import json
from pathlib import Path

from dataops_copilot.agent.services.history import search_rca_reports

from dataops_copilot.agent.models import (
    IncidentInvestigationRequest,
    IncidentRCAReport,
    RCAReport,
)
from dataops_copilot.quality.models import DataQualityIncident, QualityReport


def make_request(
    metric: str,
    affected_column: str | None,
) -> IncidentInvestigationRequest:
    """Create a small valid investigation request for testing."""
    return IncidentInvestigationRequest(
        incident=DataQualityIncident(
            metric=metric,
            observed_rate=0.01,
            threshold=0.001,
            affected_column=affected_column,
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


def make_completed_investigation(
    metric: str,
    affected_column: str | None,
) -> IncidentRCAReport:
    """Create a past RCA record for testing."""
    return IncidentRCAReport(
        request=make_request(metric, affected_column),
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


def test_search_rca_reports_returns_only_matching_metrics(tmp_path: Path) -> None:
    """Return historical records with the same incident metric."""
    current_request = make_request("negative_fare_rate", "fare_amount")

    matching_report = make_completed_investigation(
        "negative_fare_rate",
        "fare_amount",
    )
    unrelated_report = make_completed_investigation(
        "duplicate_rate",
        None,
    )

    dump_path = tmp_path / "rca_reports.json"
    dump_path.write_text(
        json.dumps(
            [
                matching_report.model_dump(mode="json"),
                unrelated_report.model_dump(mode="json"),
            ]
        ),
        encoding="utf-8",
    )

    matches = search_rca_reports(current_request, dump_path)

    assert len(matches) == 1
    assert matches[0].historical_incident.request.incident.metric == "negative_fare_rate"
    assert "same metric: negative_fare_rate" in matches[0].similarity_reasons
    assert "same affected column: fare_amount" in matches[0].similarity_reasons
