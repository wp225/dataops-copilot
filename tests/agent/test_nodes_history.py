"""Tests for the search-history langgraph node."""

from pathlib import Path

from dataops_copilot.agent.nodes.history import make_search_history_node
from dataops_copilot.agent.services.report_store import LocalJsonReportStore
from dataops_copilot.agent.state import InvestigationState
from tests.factories import make_completed_investigation, make_request


def test_search_history_node_returns_historic_matches(tmp_path: Path) -> None:
    """The node surfaces matches from the report store as node output."""
    store = LocalJsonReportStore(tmp_path / "rca_reports.json")
    store.save_report(make_completed_investigation())
    store.save_report(make_completed_investigation("duplicate_rate", None))

    search_history = make_search_history_node(store)
    result = search_history(InvestigationState(request=make_request()))
    matches = result["historical_matches"]

    assert len(matches) == 1
    assert matches[0].historical_incident.request.incident.metric == "negative_fare_rate"
