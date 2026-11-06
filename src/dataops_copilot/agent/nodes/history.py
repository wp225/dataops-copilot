"""LangGraph node for RCA retrieval."""

from collections.abc import Callable

from dataops_copilot.agent.services.history import search_rca_reports
from dataops_copilot.agent.services.report_store import ReportStore
from dataops_copilot.agent.state import InvestigationState

StateUpdate = dict[str, object]


def make_search_history_node(store: ReportStore) -> Callable[[InvestigationState], StateUpdate]:
    """Create a node that retrieves historical RCA matches."""

    def search_history(state: InvestigationState) -> StateUpdate:
        reports = store.load_reports(metric=state.request.incident.metric)
        return {"historical_matches": search_rca_reports(state.request, reports)}

    return search_history
