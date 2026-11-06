"""Tests for planned-check dispatch and the remaining catalog checks."""

import pytest
from pyspark.sql import SparkSession

from dataops_copilot.agent.checks import catalog
from dataops_copilot.agent.checks.catalog import run_check
from dataops_copilot.agent.checks.duplicate_rows import duplicate_rows
from dataops_copilot.agent.checks.models import CheckResult, PlannedCheck

SCHEMA = "payment_type int, fare_amount double"


def test_run_check_dispatches_breakdown_by(spark: SparkSession) -> None:
    df = spark.createDataFrame([(4, -5.0), (4, -2.0), (1, 3.0)], SCHEMA)
    planned = PlannedCheck(
        check_name="breakdown_by", column="fare_amount", group_by="payment_type", reason="r"
    )

    result = run_check(df, planned)

    assert result.succeeded
    assert result.metrics == {"payment_type=4": 2.0}


def test_run_check_dispatches_value_range(spark: SparkSession) -> None:
    df = spark.createDataFrame([(1, -1.0), (1, 2.0)], SCHEMA)

    result = run_check(df, PlannedCheck(check_name="value_range", column="fare_amount", reason="r"))

    assert result.metrics["negative_count"] == 1.0


def test_run_check_reports_missing_parameters() -> None:
    df = None

    result = run_check(
        df, PlannedCheck(check_name="breakdown_by", column="fare_amount", reason="r")
    )

    assert not result.succeeded
    assert result.error == "breakdown_by requires 'column' and 'group_by'."
    assert result.params == {"column": "fare_amount"}

    result = run_check(df, PlannedCheck(check_name="value_range", reason="r"))
    assert result.error == "value_range requires 'column'."


def test_run_check_turns_exceptions_into_failed_results(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*_: object) -> None:
        message = "executor lost"
        raise RuntimeError(message)

    monkeypatch.setattr(catalog, "value_range", explode)
    df = None

    result = run_check(df, PlannedCheck(check_name="value_range", column="fare_amount", reason="r"))

    assert not result.succeeded
    assert result.error == "RuntimeError: executor lost"


def test_duplicate_rows_counts_exact_duplicates(spark: SparkSession) -> None:
    df = spark.createDataFrame([(1, 1.0), (1, 1.0), (2, 2.0), (3, 3.0)], SCHEMA)

    result = duplicate_rows(df)

    assert result.metrics == {
        "row_count": 4.0,
        "distinct_count": 3.0,
        "duplicate_count": 1.0,
        "duplicate_rate": 0.25,
    }


def test_duplicate_rows_handles_empty_dataframe(spark: SparkSession) -> None:
    result = duplicate_rows(spark.createDataFrame([], SCHEMA))

    assert result.metrics["duplicate_rate"] == 0.0


def test_check_result_describe_is_stable() -> None:
    result = CheckResult(
        check_name="breakdown_by",
        params={"group_by": "payment_type", "column": "fare_amount"},
        metrics={},
        succeeded=True,
    )

    assert result.describe() == "breakdown_by(column=fare_amount, group_by=payment_type)"
