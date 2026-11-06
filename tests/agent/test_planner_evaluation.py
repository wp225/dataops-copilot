"""Tests for the LangSmith planner evaluation target and evaluators."""

from typing import Any

from dataops_copilot.agent.checks.models import PlannedCheck
from dataops_copilot.agent.evaluations.datasets import (
    load_planner_evaluation_cases,
)
from dataops_copilot.agent.evaluations.planner import (
    evaluate_read_only_plan,
    evaluate_required_checks,
    make_planner_target,
)
from dataops_copilot.agent.models import AnalysisPlan, PlanningContext
from tests.factories import make_plan


def _plan_output(plan: AnalysisPlan) -> dict[str, Any]:
    return {"analysis_plan": plan.model_dump(mode="json")}


def test_planner_target_serializes_planner_output() -> None:
    """Adapt a typed planner result into LangSmith-compatible JSON."""
    case = load_planner_evaluation_cases("evals/rca_planner_v2.json")[0]
    expected_plan = make_plan()

    def fake_planner(context: PlanningContext) -> AnalysisPlan:
        assert context.request == case.request
        assert context.historical_matches == []
        return expected_plan

    target = make_planner_target(fake_planner)

    result = target(
        {
            "request": case.request.model_dump(mode="json"),
            "historical_matches": [],
        }
    )

    assert result == _plan_output(expected_plan)


def test_read_only_evaluator_accepts_safe_plan() -> None:
    """Accept a plan containing only inspection steps."""
    assert evaluate_read_only_plan(outputs=_plan_output(make_plan()))["score"] == 1


def test_read_only_evaluator_rejects_mutating_plan() -> None:
    """Reject a plan whose free text proposes modifying the dataset."""
    plan = make_plan(
        PlannedCheck(
            check_name="value_range",
            column="fare_amount",
            reason="Then DELETE rows with negative fare amounts.",
        )
    )

    result = evaluate_read_only_plan(outputs=_plan_output(plan))

    assert result["score"] == 0
    assert "delete" in result["comment"]


def test_read_only_evaluator_rejects_missing_plan() -> None:
    """Reject output when the planner failed to produce a plan."""
    result = evaluate_read_only_plan(outputs={})

    assert result["score"] == 0
    assert "No analysis plan" in result["comment"]


def test_required_checks_evaluator_scores_coverage() -> None:
    plan = make_plan(
        PlannedCheck(check_name="value_range", column="fare_amount", reason="r"),
    )

    result = evaluate_required_checks(
        outputs=_plan_output(plan),
        reference_outputs={"required_checks": ["value_range:fare_amount", "duplicate_rows"]},
    )

    assert result["score"] == 0.5
    assert result["comment"] == "Missing: duplicate_rows."


def test_required_checks_evaluator_ignores_column_when_not_required() -> None:
    result = evaluate_required_checks(
        outputs=_plan_output(make_plan()),
        reference_outputs={"required_checks": ["breakdown_by"]},
    )

    assert result["score"] == 1


def test_required_checks_evaluator_handles_missing_inputs() -> None:
    assert evaluate_required_checks(outputs=None)["score"] == 0
    assert evaluate_required_checks(outputs=_plan_output(make_plan()))["score"] == 1
