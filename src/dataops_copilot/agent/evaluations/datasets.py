"""Load version-controlled planner evaluation cases."""

import json
from pathlib import Path

from dataops_copilot.agent.evaluations.models import PlannerEvaluationCase


def load_planner_evaluation_cases(
    file_path: Path | str,
) -> list[PlannerEvaluationCase]:
    """Load and validate planner evaluation cases from a JSON file."""
    raw_cases = json.loads(Path(file_path).read_text(encoding="utf-8"))

    if not isinstance(raw_cases, list):
        message = "Planner evaluation data must be a JSON list."
        raise TypeError(message)

    return [PlannerEvaluationCase.model_validate(raw_case) for raw_case in raw_cases]
