"""Check describing the value range of one numeric column."""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from dataops_copilot.agent.checks.models import CheckResult

CHECK_NAME = "value_range"


def value_range(df: DataFrame, column: str) -> CheckResult:
    """Performs value range checks on column."""
    if column not in df.columns:
        return CheckResult(
            check_name=CHECK_NAME,
            succeeded=False,
            metrics={},
            params={"column": ""},
            error=f"Column '{column}' does not exist.",
        )

    aggregate = df.agg(
        F.min(col=column).alias("min"),
        F.max(col=column).alias("max"),
        F.count(F.lit(1)).alias("row_count"),
        F.count(F.when(F.col(col=column) < 0, 1)).alias("negative_count"),
        F.count(F.when(F.col(column).isNull(), 1)).alias("null_count"),
    ).first()
    if aggregate is None:
        message = "Spark aggregation unexpectedly returned no metrics row."
        raise RuntimeError(message)

    metrics = {}
    for key, value in aggregate.asDict().items():
        if value is not None:
            metrics[key] = float(value)

    return CheckResult(
        check_name=CHECK_NAME, metrics=metrics, succeeded=True, params={"column": column}
    )
