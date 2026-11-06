"""Tests for the Claude-backed services, using a fake chat model."""

from typing import Any

from pydantic import BaseModel

from dataops_copilot.agent.checks.models import CheckResult
from dataops_copilot.agent.models import (
    AnalysisPlan,
    EvidenceAssessment,
    InvestigationContext,
    PlanningContext,
    RCAReport,
)
from dataops_copilot.agent.services.assessor import make_claude_assessor
from dataops_copilot.agent.services.planner import make_claude_planner, render_planning_prompt
from dataops_copilot.agent.services.report_writer import make_claude_report_writer
from tests.factories import make_assessment, make_plan, make_rca_report, make_request


class FakeStructured:
    def __init__(self, response: BaseModel, calls: list[Any]) -> None:
        self.response = response
        self.calls = calls

    def invoke(self, messages: list[Any]) -> dict[str, Any]:
        self.calls.append(messages)
        return self.response.model_dump()


class FakeChatModel:
    def __init__(self, response: BaseModel) -> None:
        self.response = response
        self.calls: list[Any] = []
        self.structured_with: list[tuple[type, str]] = []

    def with_structured_output(self, schema: type, method: str) -> FakeStructured:
        self.structured_with.append((schema, method))
        return FakeStructured(self.response, self.calls)


def test_planner_uses_native_structured_output_and_renders_context() -> None:
    llm = FakeChatModel(make_plan())
    planner = make_claude_planner(llm)  # ty: ignore[invalid-argument-type]

    plan = planner(PlanningContext(request=make_request(), open_questions=["Which vendor?"]))

    assert isinstance(plan, AnalysisPlan)
    assert llm.structured_with == [(AnalysisPlan, "json_schema")]
    system, human = llm.calls[0]
    assert "breakdown_by(column, group_by, condition)" in system.content
    assert "Which vendor?" in human.content
    assert "Dataset columns: fare_amount, payment_type" in human.content


def test_planning_prompt_includes_prior_results() -> None:
    prior = CheckResult(
        check_name="value_range",
        params={"column": "fare_amount"},
        metrics={"min": -3.0},
        succeeded=True,
    )

    prompt = render_planning_prompt(PlanningContext(request=make_request(), prior_results=[prior]))

    assert '"min": -3.0' in prompt


def test_assessor_and_writer_parse_structured_replies() -> None:
    context = InvestigationContext(request=make_request())

    assessment = make_claude_assessor(FakeChatModel(make_assessment(sufficient=True)))(context)  # ty: ignore[invalid-argument-type]
    report = make_claude_report_writer(FakeChatModel(make_rca_report()))(context)  # ty: ignore[invalid-argument-type]

    assert isinstance(assessment, EvidenceAssessment)
    assert isinstance(report, RCAReport)
