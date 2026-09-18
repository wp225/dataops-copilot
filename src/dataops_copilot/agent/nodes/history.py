"""LangGraph node for RCA retrieval."""

from collections.abc import Callable
from pathlib import Path

from dataops_copilot.agent.services.history import search_rca_reports
from dataops_copilot.agent.state import InvestigationState

StateUpdate = dict[str, object]


def make_search_history_node(rca_dump_path: str | Path):  # noqa: ANN201
    """Create a node that retrieves historical RCA matches."""

    def search_history(state: InvestigationState) -> StateUpdate:
        historic_matches = search_rca_reports(
            investigation_request=state.request, rca_dump_path=rca_dump_path
        )
        return {"historical_matches": historic_matches}

    return search_history
