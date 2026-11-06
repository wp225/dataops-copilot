"""Check counting exact duplicate rows."""

from pyspark.sql import DataFrame

from dataops_copilot.agent.checks.models import CheckResult

CHECK_NAME = "duplicate_rows"


def duplicate_rows(df: DataFrame) -> CheckResult:
    """Return total, distinct and duplicate row counts for the dataset."""
    row_count = df.count()
    distinct_count = df.distinct().count()
    duplicate_count = row_count - distinct_count
    duplicate_rate = duplicate_count / row_count if row_count else 0.0

    return CheckResult(
        check_name=CHECK_NAME,
        params={},
        metrics={
            "row_count": float(row_count),
            "distinct_count": float(distinct_count),
            "duplicate_count": float(duplicate_count),
            "duplicate_rate": duplicate_rate,
        },
        succeeded=True,
    )
