"""Claude-backed evidence assessment."""

from collections.abc import Callable

from langchain_anthropic import ChatAnthropic

from dataops_copilot.agent.models import EvidenceAssessment, InvestigationContext
from dataops_copilot.agent.services.llm import make_structured_call

Assessor = Callable[[InvestigationContext], EvidenceAssessment]

SYSTEM_PROMPT = """
You assess evidence in a data-quality root-cause investigation.

Decide whether the check results gathered so far directly support one root
cause for the incident. Base the judgement on the metrics in the check results,
not on the hypotheses alone; failed checks are not evidence. Historical cases
can raise or lower confidence but cannot by themselves make evidence sufficient.
If the evidence is insufficient, list the open questions and what evidence
would resolve them.
"""


def make_claude_assessor(llm: ChatAnthropic) -> Assessor:
    """Create an evidence assessor backed by the supplied Claude model."""
    call = make_structured_call(llm, EvidenceAssessment, SYSTEM_PROMPT)

    def claude_assessor(context: InvestigationContext) -> EvidenceAssessment:
        return call(f"Investigation so far:\n{context.model_dump_json(indent=2)}")

    return claude_assessor
