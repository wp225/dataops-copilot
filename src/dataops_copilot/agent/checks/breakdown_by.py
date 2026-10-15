"""Groupby for drill down."""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from dataops_copilot.agent.checks.models import CheckResult

CHECK_NAME = "breakdown_by"


def breakdown_by(df: DataFrame, column: str, group_by: str) -> CheckResult:
    """Return the count of negative values in column for each group."""
    if column not in df.columns:
        return CheckResult(
            check_name=CHECK_NAME,
            succeeded=False,
            metrics={},
            params={"column": column, "group_by": group_by},
            error=f"Column '{column}' does not exist.",
        )
    if group_by not in df.columns:
        return CheckResult(
            check_name=CHECK_NAME,
            succeeded=False,
            metrics={},
            params={"column": column, "group_by": group_by},
            error=f"Column '{group_by}' does not exist for groupby",
        )

    cleaned_metrics = {}
    metrics = df.filter(F.col(col=column) < 0).groupBy(group_by).count().collect()
    for row in metrics:
        cleaned_metrics[f"{group_by}={row[group_by]}"] = float(row["count"])
    return CheckResult(
        check_name=CHECK_NAME,
        metrics=cleaned_metrics,
        succeeded=True,
        params={"column": column, "group_by": group_by},
    )
