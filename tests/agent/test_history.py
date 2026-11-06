"""Tests for historical RCA retrieval."""

from dataops_copilot.agent.services.history import search_rca_reports
from tests.factories import make_completed_investigation, make_request


def test_search_rca_reports_returns_only_matching_metrics() -> None:
    """Return historical records with the same incident metric."""
    matches = search_rca_reports(
        make_request("negative_fare_rate", "fare_amount"),
        [
            make_completed_investigation("negative_fare_rate", "fare_amount"),
            make_completed_investigation("duplicate_rate", None),
        ],
    )

    assert len(matches) == 1
    assert matches[0].historical_incident.request.incident.metric == "negative_fare_rate"
    assert "same metric: negative_fare_rate" in matches[0].similarity_reasons
    assert "same affected column: fare_amount" in matches[0].similarity_reasons


def test_search_rca_reports_ranks_closer_matches_first() -> None:
    weak = make_completed_investigation("negative_fare_rate", "total_amount", "green-taxi")
    strong = make_completed_investigation("negative_fare_rate", "fare_amount", "yellow-taxi")

    matches = search_rca_reports(make_request(), [weak, strong])

    assert [match.historical_incident for match in matches] == [strong, weak]
