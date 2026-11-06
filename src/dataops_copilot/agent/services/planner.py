"""Claude-backed investigation planner."""

import json
from collections.abc import Callable

from langchain_anthropic import ChatAnthropic

from dataops_copilot.agent.checks.catalog import CATALOG_DESCRIPTION
from dataops_copilot.agent.models import AnalysisPlan, PlanningContext
from dataops_copilot.agent.services.llm import available_columns, make_structured_call

Planner = Callable[[PlanningContext], AnalysisPlan]

SYSTEM_PROMPT = f"""
You are a data-quality root-cause analysis planner.

Create an evidence-aware investigation plan for the supplied incident.
Treat likely causes as hypotheses, not confirmed facts, and give at most three.
For each hypothesis choose checks from the catalog below that would confirm or
refute it. Only use column names that exist in the dataset.
Use the incident, quality report, historical cases, and any results from
earlier rounds. Do not repeat a check that already ran; plan checks that
answer the open questions instead.
Do not generate code or recommend modifying data.
{CATALOG_DESCRIPTION}
"""


def render_planning_prompt(context: PlanningContext) -> str:
    """Render the planner's user message."""
    historical_cases = [match.model_dump(mode="json") for match in context.historical_matches]
    prior_results = [result.model_dump(mode="json") for result in context.prior_results]
    return (
        f"Investigation request:\n{context.request.model_dump_json(indent=2)}\n\n"
        f"Dataset columns: {available_columns(context.request.quality_report.null_rates)}\n\n"
        f"Historical matches:\n{json.dumps(historical_cases, indent=2)}\n\n"
        f"Results from earlier rounds:\n{json.dumps(prior_results, indent=2)}\n\n"
        f"Open questions:\n{json.dumps(context.open_questions, indent=2)}"
    )


def make_claude_planner(llm: ChatAnthropic) -> Planner:
    """Create a planner backed by the supplied Claude model."""
    call = make_structured_call(llm, AnalysisPlan, SYSTEM_PROMPT)

    def claude_planner(context: PlanningContext) -> AnalysisPlan:
        """Return an investigation plan from Claude."""
        return call(render_planning_prompt(context))

    return claude_planner
