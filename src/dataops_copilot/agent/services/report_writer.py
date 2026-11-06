"""Claude-backed RCA report writer."""

from collections.abc import Callable

from langchain_anthropic import ChatAnthropic

from dataops_copilot.agent.models import InvestigationContext, RCAReport
from dataops_copilot.agent.services.llm import make_structured_call

ReportWriter = Callable[[InvestigationContext], RCAReport]

SYSTEM_PROMPT = """
You write the final root-cause analysis report for a data-quality incident.

State the most likely cause and the confidence the evidence supports. Cite
concrete metrics from the check results as evidence. If the evidence is not
sufficient, say the cause is unconfirmed, set confidence to low, and require
escalation to a human. Recommendations must be advisory: describe what an
engineer should verify or fix upstream; never instruct anyone to delete or
overwrite data.
"""


def make_claude_report_writer(llm: ChatAnthropic) -> ReportWriter:
    """Create a report writer backed by the supplied Claude model."""
    call = make_structured_call(llm, RCAReport, SYSTEM_PROMPT)

    def claude_report_writer(context: InvestigationContext) -> RCAReport:
        return call(f"Completed investigation:\n{context.model_dump_json(indent=2)}")

    return claude_report_writer
