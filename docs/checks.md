# Check catalog

The check catalog is the only way an investigation can touch the data. Each
check is a reviewed PySpark function that reads the batch and returns a
`CheckResult` of named numeric metrics. Claude picks checks and their
parameters. It cannot write queries of its own.

## Checks

### `value_range`

Summary statistics for one numeric column.

| Parameter | Required | |
| --- | --- | --- |
| `column` | yes | Column to summarize. |

**Metrics:** `min`, `max`, `row_count`, `negative_count`, `null_count`.

```json title="Example: fare_amount, January 2026"
{"min": -2555.2, "max": 2555.2, "row_count": 3724889.0,
 "negative_count": 39463.0, "null_count": 0.0}
```

### `breakdown_by`

Counts rows that match a condition on `column`, grouped by another column.
Returns the 25 largest groups, largest first.

| Parameter | Required | |
| --- | --- | --- |
| `column` | yes | Column the condition applies to. |
| `group_by` | yes | Column to group the matching rows by. |
| `condition` | no | `negative` (`column < 0`, the default), `non_positive` (`column <= 0`) or `null` (`column IS NULL`). |

**Metrics:** one entry per group, named `<group_by>=<value>`.

```json title="Example: negative fare_amount by payment_type"
{"payment_type=4": 26039.0, "payment_type=2": 8633.0, "payment_type=3": 4492.0,
 "payment_type=1": 267.0, "payment_type=0": 32.0}
```

### `duplicate_rows`

Exact duplicate rows across the whole batch. Takes no parameters.

**Metrics:** `row_count`, `distinct_count`, `duplicate_count`, `duplicate_rate`.

## The planned-check model

The planner emits each check as a flat `PlannedCheck`:

```python
class PlannedCheck(BaseModel):
    check_name: Literal["value_range", "breakdown_by", "duplicate_rows"]
    column: str | None = None
    group_by: str | None = None
    condition: Literal["negative", "non_positive", "null"] | None = None
    reason: str
```

The model is flat rather than a discriminated union, because Claude's
structured outputs do not enforce `const` values. Per-check rules, such as
"`breakdown_by` needs `column` and `group_by`", are checked in
`checks/catalog.py` when the check runs.

## Failure handling

`run_check` never raises. Each of these returns a `CheckResult` with
`succeeded: false` and an `error` message the assessor can read:

- a required parameter is missing, for example `breakdown_by requires 'column' and 'group_by'.`
- the column doesn't exist, for example `Column 'fare_amt' does not exist.`
- any Spark error, reported as `<ExceptionType>: <message>`
- the batch can't be loaded, reported as `Could not load batch data: ...`

Checks that have already succeeded are not run again in later rounds, so a
replan costs only the new checks.

## Adding a check

1. Write a function in `src/dataops_copilot/agent/checks/` that takes a
   `DataFrame` and its parameters and returns a `CheckResult`. Keep it
   read-only: aggregations only, with no writes and no `collect()` of raw rows.
2. Add its name to `CheckName` in `checks/models.py`. Add any new parameters
   to `PlannedCheck` as optional fields.
3. Add a `case` in `run_check` in `checks/catalog.py` that validates the
   parameters and calls the function.
4. Describe it in `CATALOG_DESCRIPTION` in the same file. The planner's
   system prompt embeds this text, so a check that isn't described there is
   never planned.
5. Add a test, and a case with `required_checks` to
   [`evals/rca_planner_v2.json`](evaluation.md) if the planner should pick
   the new check.
