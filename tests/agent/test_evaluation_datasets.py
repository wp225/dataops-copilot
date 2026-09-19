"""Tests for planner evaluation dataset loading."""

from pathlib import Path

from dataops_copilot.agent.evaluations.datasets import (
    load_planner_evaluation_cases,
)


def test_load_planner_evaluation_cases_reads_golden_case() -> None:
    """Load the version-controlled planner evaluation dataset."""
    dataset_path = Path("evals/rca_planner_v1.json")

    cases = load_planner_evaluation_cases(dataset_path)

    assert len(cases) == 1
    assert cases[0].case_id == "negative-fares-no-history"
    assert cases[0].historical_matches == []
    assert cases[0].escalation_expected is False
