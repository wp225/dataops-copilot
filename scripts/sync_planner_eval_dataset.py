"""Create the first LangSmith dataset for RCA planner evaluation."""

from langsmith import Client

from dataops_copilot.agent.evaluations.datasets import (
    load_planner_evaluation_cases,
)

DATASET_NAME = "dataops-copilot-rca-planner-v1"
DATASET_PATH = "evals/rca_planner_v1.json"


def main() -> None:
    """Create the LangSmith dataset when it does not already exist."""
    client = Client()
    cases = load_planner_evaluation_cases(DATASET_PATH)

    existing_datasets = list(client.list_datasets(dataset_name=DATASET_NAME))
    if existing_datasets:
        print(f"Dataset already exists: {DATASET_NAME}")
        return

    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="Golden cases for DataOps Copilot RCA planner evaluation.",
    )

    examples = [
        {
            "inputs": {
                "request": case.request.model_dump(mode="json"),
                "historical_matches": [
                    match.model_dump(mode="json") for match in case.historical_matches
                ],
            },
            "outputs": {
                "expected_cause_categories": case.expected_cause_categories,
                "required_checks": case.required_checks,
                "escalation_expected": case.escalation_expected,
            },
            "metadata": {
                "case_id": case.case_id,
            },
        }
        for case in cases
    ]

    client.create_examples(
        dataset_id=dataset.id,
        examples=examples,
    )
    print(f"Created dataset: {DATASET_NAME}")


if __name__ == "__main__":
    main()
