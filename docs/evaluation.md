# Planner evaluation

The planner is the step most likely to regress when the prompt, the model or
the effort level changes. It is evaluated offline against a small golden
dataset, using [LangSmith](https://smith.langchain.com/) experiments.

## Golden cases

`evals/rca_planner_v2.json` holds the cases. Each one gives the planner a full
`PlanningContext` input and states what a good plan must contain:

```json
{
  "case_id": "negative-fares-no-history",
  "request": {
    "incident": {"metric": "negative_fare_rate", "observed_rate": 0.01,
                 "threshold": 0.001, "affected_column": "fare_amount"},
    "quality_report": {"row_count": 1000, "negative_fare_rate": 0.01, "...": "..."},
    "dataset_name": "yellow_taxi",
    "batch_id": "batch-001"
  },
  "historical_matches": [],
  "expected_cause_categories": ["refund_or_sign_mapping"],
  "required_checks": ["value_range:fare_amount", "breakdown_by:fare_amount"],
  "escalation_expected": false
}
```

| Case | Required checks |
| --- | --- |
| `negative-fares-no-history` | `value_range:fare_amount`, `breakdown_by:fare_amount` |
| `negative-fares-with-refund-history` | `breakdown_by:fare_amount` |
| `zero-trip-distance` | `value_range:trip_distance`, `breakdown_by:trip_distance` |
| `null-passenger-count` | `breakdown_by:passenger_count` |
| `duplicate-rows` | `duplicate_rows` |

## Evaluators

| Key | Score | Passes when |
| --- | --- | --- |
| `read_only_checks` | 0 or 1 | The serialized plan contains no mutating terms (`delete`, `drop`, `overwrite`, `.write` and others), including in the free-text reasons. |
| `required_checks` | 0 to 1 | The share of `required_checks` the plan includes. `check_name:column` must match both the name and the column; a bare `check_name` matches any column. |

Both live in `src/dataops_copilot/agent/evaluations/planner.py` and are unit
tested without network access.

## Running an experiment

Set `LANGSMITH_API_KEY` and `ANTHROPIC_API_KEY` in `.env`, then:

```bash
# Once, or after editing the JSON: create the LangSmith dataset
uv run python scripts/sync_planner_eval_dataset.py

# Run the planner against every case
uv run python scripts/run_planner_eval.py
```

The experiment uses `DATAOPS_ANTHROPIC_MODEL`, so you can compare models by
running it twice with different values and comparing the two experiments in
LangSmith.
