"""Run the RCA planner against the LangSmith golden dataset."""

import os

from langchain_anthropic import ChatAnthropic
from langsmith import Client

from dataops_copilot.agent.evaluations.planner import (
    evaluate_read_only_plan,
    make_planner_target,
)
from dataops_copilot.agent.services.planner import make_claude_planner

DATASET_NAME = "dataops-copilot-rca-planner-v1"


def main() -> None:
    """Run a manual LangSmith evaluation experiment."""
    model_name = os.environ["ANTHROPIC_MODEL"]

    llm = ChatAnthropic(model=model_name)
    planner = make_claude_planner(llm)
    target = make_planner_target(planner)

    client = Client()
    results = client.evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[evaluate_read_only_plan],
        experiment_prefix="rca-planner-v1",
        max_concurrency=1,
    )

    print(results)


if __name__ == "__main__":
    main()
