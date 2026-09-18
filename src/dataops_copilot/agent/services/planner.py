"""Claude-backed investigation planner."""

import json
from collections.abc import Callable

from langchain_anthropic import ChatAnthropic

from dataops_copilot.agent.models import (
    AnalysisPlan,
    HistoricalIncidentMatch,
    IncidentInvestigationRequest,
)

Planner = Callable[
    [IncidentInvestigationRequest, list[HistoricalIncidentMatch]],
    AnalysisPlan,
]

SYSTEM_PROMPT = """
You are a data-quality root-cause analysis planner.

Create an evidence-aware investigation plan for the supplied incident.
Treat likely causes as hypotheses, not confirmed facts.
Propose only read-only data checks.
Use the incident, quality report, and historical cases provided.
Do not generate Python code or recommend modifying data.
"""


def make_claude_planner(llm: ChatAnthropic) -> Planner:
    """Create a planner backed by the supplied Claude model."""
    structured_llm = llm.with_structured_output(AnalysisPlan)

    def claude_planner(
        investigation_request: IncidentInvestigationRequest,
        historical_matches: list[HistoricalIncidentMatch],
    ) -> AnalysisPlan:
        """Return an investigation plan from Claude."""
        historical_cases = [match.model_dump(mode="json") for match in historical_matches]
        prompt = f"""
        {SYSTEM_PROMPT}
        Investigation Request: {investigation_request.model_dump_json(indent=2)}
        Historical Matches : {json.dumps(historical_cases)}
        """

        response = structured_llm.invoke(prompt)
        return AnalysisPlan.model_validate(response)

    return claude_planner
