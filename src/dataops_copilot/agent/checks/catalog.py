"""Dispatch planned checks to their read-only implementations."""

from pyspark.sql import DataFrame

from dataops_copilot.agent.checks.breakdown_by import breakdown_by
from dataops_copilot.agent.checks.duplicate_rows import duplicate_rows
from dataops_copilot.agent.checks.models import CheckResult, PlannedCheck
from dataops_copilot.agent.checks.value_range import value_range

CATALOG_DESCRIPTION = """
Available checks (the only checks you may plan):
- value_range(column): min, max, row_count, negative_count and null_count of one numeric column.
- breakdown_by(column, group_by, condition): rows matching a condition on `column`, counted per
  value of `group_by` (top 25 groups). condition is one of "negative" (column < 0, the default),
  "non_positive" (column <= 0) or "null" (column IS NULL).
- duplicate_rows(): total, distinct and duplicate row counts for the whole batch.
"""


def _failed(planned: PlannedCheck, error: str) -> CheckResult:
    params = {
        key: value
        for key, value in planned.model_dump(include={"column", "group_by", "condition"}).items()
        if value is not None
    }
    return CheckResult(
        check_name=planned.check_name,
        params=params,
        metrics={},
        succeeded=False,
        error=error,
    )


def run_check(df: DataFrame, planned: PlannedCheck) -> CheckResult:
    """Run one planned check. Never raises: failures become failed results."""
    try:
        match planned.check_name:
            case "value_range":
                if planned.column is None:
                    return _failed(planned, "value_range requires 'column'.")
                return value_range(df, planned.column)
            case "breakdown_by":
                if planned.column is None or planned.group_by is None:
                    return _failed(planned, "breakdown_by requires 'column' and 'group_by'.")
                return breakdown_by(
                    df, planned.column, planned.group_by, planned.condition or "negative"
                )
            case "duplicate_rows":
                return duplicate_rows(df)
    except Exception as error:
        return _failed(planned, f"{type(error).__name__}: {error}")
