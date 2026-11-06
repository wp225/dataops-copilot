"""Groupby for drill down."""

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F

from dataops_copilot.agent.checks.models import BreakdownCondition, CheckResult

CHECK_NAME = "breakdown_by"
MAX_GROUPS = 25


def _condition_expression(column: str, condition: BreakdownCondition) -> Column:
    """Return the Spark filter selecting rows that match the condition."""
    if condition == "negative":
        return F.col(column) < 0
    if condition == "non_positive":
        return F.col(column) <= 0
    return F.col(column).isNull()


def breakdown_by(
    df: DataFrame,
    column: str,
    group_by: str,
    condition: BreakdownCondition = "negative",
) -> CheckResult:
    """Return how many rows match the condition on column, for each group.

    Only the largest MAX_GROUPS groups are returned, to keep evidence compact.
    """
    params = {"column": column, "group_by": group_by}
    if condition != "negative":
        params["condition"] = condition

    if column not in df.columns:
        return CheckResult(
            check_name=CHECK_NAME,
            succeeded=False,
            metrics={},
            params=params,
            error=f"Column '{column}' does not exist.",
        )
    if group_by not in df.columns:
        return CheckResult(
            check_name=CHECK_NAME,
            succeeded=False,
            metrics={},
            params=params,
            error=f"Column '{group_by}' does not exist for groupby",
        )

    rows = (
        df.filter(_condition_expression(column, condition))
        .groupBy(group_by)
        .count()
        .orderBy(F.desc("count"))
        .limit(MAX_GROUPS)
        .collect()
    )
    metrics = {f"{group_by}={row[group_by]}": float(row["count"]) for row in rows}
    return CheckResult(
        check_name=CHECK_NAME,
        metrics=metrics,
        succeeded=True,
        params=params,
    )
