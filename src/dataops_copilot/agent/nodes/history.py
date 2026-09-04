"""Langgraph node for RCA retreval."""

from pathlib import Path

from dataops_copilot.agent.models import (
    HistoricalIncidentMatch,
    IncidentInvestigationRequest,
    IncidentRCAReport,
)
from dataops_copilot.agent.services.history import search_rca_reports
from dataops_copilot.agent.state import InvestigationState


def make_search_history_node(
    rca_dump_path: str | Path,
) -> callable[[IncidentInvestigationRequest], dict[str, list[HistoricalIncidentMatch]]]:
    """Create a node that retrives historical RCA matches."""

    def search_history(state: InvestigationState) -> dict[str, list[HistoricalIncidentMatch]]:
        historic_matches: list[HistoricalIncidentMatch] = search_rca_reports(
            investigation_request=state.request, rca_dump_path=rca_dump_path
        )
        return {"historic_matches": historic_matches}

    return search_history
