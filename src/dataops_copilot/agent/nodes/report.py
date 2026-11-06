"""Node that writes the final RCA report."""

from collections.abc import Callable

from dataops_copilot.agent.models import IncidentRCAReport
from dataops_copilot.agent.services.report_writer import ReportWriter
from dataops_copilot.agent.state import InvestigationState

StateUpdate = dict[str, object]


def make_write_report_node(writer: ReportWriter) -> Callable[[InvestigationState], StateUpdate]:
    """Create a node that drafts the report with the LLM, then fixes the factual fields.

    Counts, executed checks and escalation are set from state rather than trusted
    to the model: an investigation that ends without sufficient evidence always
    escalates.
    """

    def write_report(state: InvestigationState) -> StateUpdate:
        draft = writer(state.to_context())
        escalate = draft.escalation_required or not state.evidence_sufficient
        report = draft.model_copy(
            update={
                "previous_similar_incidents": len(state.historical_matches),
                "analyses_executed": [
                    result.describe() for result in state.check_results if result.succeeded
                ],
                "escalation_required": escalate,
                "confidence": "low" if not state.evidence_sufficient else draft.confidence,
            }
        )
        return {"final_result": IncidentRCAReport(request=state.request, report=report)}

    return write_report
