"""Run the RCA planner against the LangSmith golden dataset."""

import os

from langsmith import Client

from dataops_copilot.agent.evaluations.planner import (
    evaluate_read_only_plan,
    evaluate_required_checks,
    make_planner_target,
)
from dataops_copilot.agent.services.llm import DEFAULT_MODEL, make_chat_model
from dataops_copilot.agent.services.planner import make_claude_planner

DATASET_NAME = "dataops-copilot-rca-planner-v2"


def main() -> None:
    """Run a manual LangSmith evaluation experiment."""
    model_name = os.environ.get("DATAOPS_ANTHROPIC_MODEL", DEFAULT_MODEL)

    llm = make_chat_model(model_name)
    planner = make_claude_planner(llm)
    target = make_planner_target(planner)

    client = Client()
    results = client.evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[evaluate_read_only_plan, evaluate_required_checks],
        experiment_prefix="rca-planner-v2",
        max_concurrency=1,
    )

    print(results)


if __name__ == "__main__":
    main()
