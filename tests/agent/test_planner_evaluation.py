"""Tests for the LangSmith planner evaluation target."""

from dataops_copilot.agent.evaluations.datasets import (
    load_planner_evaluation_cases,
)
from dataops_copilot.agent.evaluations.planner import (
    evaluate_read_only_plan,
    make_planner_target,
)
from dataops_copilot.agent.models import AnalysisHypothesis, AnalysisPlan


def test_planner_target_serializes_planner_output() -> None:
    """Adapt a typed planner result into LangSmith-compatible JSON."""
    case = load_planner_evaluation_cases("evals/rca_planner_v1.json")[0]
    expected_plan = AnalysisPlan(
        analysis_goal="Identify why fare amounts are negative.",
        hypotheses=[
            AnalysisHypothesis(
                likely_cause="Refund values may be mapped into fare_amount.",
                rationale="The negative-fare rate exceeds the policy threshold.",
                likelihood="medium",
                checks_to_run=[
                    "Break down negative fares by payment type.",
                ],
            )
        ],
    )

    def fake_planner(request: any, historical_matches: any) -> AnalysisPlan:
        assert request == case.request
        assert historical_matches == []
        return expected_plan

    target = make_planner_target(fake_planner)

    result = target(
        {
            "request": case.request.model_dump(mode="json"),
            "historical_matches": [],
        }
    )

    assert result == {"analysis_plan": expected_plan.model_dump(mode="json")}


def test_read_only_evaluator_accepts_safe_plan() -> None:
    """Accept a plan containing only inspection steps."""
    result = evaluate_read_only_plan(
        outputs={
            "analysis_plan": {
                "analysis_goal": "Investigate negative fares.",
                "hypotheses": [
                    {
                        "likely_cause": "Refund mapping issue.",
                        "rationale": "Negative fares exceed the threshold.",
                        "likelihood": "medium",
                        "checks_to_run": [
                            "Compare negative fares by payment type.",
                        ],
                    }
                ],
            }
        }
    )

    assert result["score"] == 1


def test_read_only_evaluator_rejects_mutating_plan() -> None:
    """Reject a plan that proposes modifying the dataset."""
    result = evaluate_read_only_plan(
        outputs={
            "analysis_plan": {
                "analysis_goal": "Investigate negative fares.",
                "hypotheses": [
                    {
                        "likely_cause": "Refund mapping issue.",
                        "rationale": "Negative fares exceed the threshold.",
                        "likelihood": "medium",
                        "checks_to_run": [
                            "DELETE rows with negative fare amounts.",
                        ],
                    }
                ],
            }
        }
    )

    assert result["score"] == 0
    assert "delete" in result["comment"]


def test_read_only_evaluator_rejects_missing_plan() -> None:
    """Reject output when the planner failed to produce a plan."""
    result = evaluate_read_only_plan(outputs={})

    assert result["score"] == 0
    assert "No analysis plan" in result["comment"]
