from pyspark.sql import SparkSession

from dataops_copilot.agent.checks.breakdown_by import breakdown_by

SCHEMA = "VendorID int, fare_amount double"


def test_breakdown_by_counts_negative_values_per_group(spark: SparkSession) -> None:
    df = spark.createDataFrame(
        [(1, -5.0), (1, -2.0), (1, 8.0), (2, 10.0), (2, -1.0), (3, 4.0)],
        SCHEMA,
    )

    result = breakdown_by(df, "fare_amount", "VendorID")

    assert result.succeeded
    assert result.check_name == "breakdown_by"
    assert result.metrics == {"VendorID=1": 2.0, "VendorID=2": 1.0}
    assert result.params == {"column": "fare_amount", "group_by": "VendorID"}


def test_breakdown_by_returns_empty_metrics_without_negative_values(
    spark: SparkSession,
) -> None:
    df = spark.createDataFrame([(1, 5.0), (2, 10.0)], SCHEMA)

    result = breakdown_by(df, "fare_amount", "VendorID")

    assert result.succeeded
    assert result.metrics == {}


def test_breakdown_by_fails_for_missing_column(spark: SparkSession) -> None:
    df = spark.createDataFrame([(1, -5.0)], SCHEMA)

    result = breakdown_by(df, "tip_amount", "VendorID")

    assert not result.succeeded
    assert result.metrics == {}
    assert result.params == {"column": "tip_amount", "group_by": "VendorID"}
    assert result.error == "Column 'tip_amount' does not exist."


def test_breakdown_by_fails_for_missing_group_by_column(spark: SparkSession) -> None:
    df = spark.createDataFrame([(1, -5.0)], SCHEMA)

    result = breakdown_by(df, "fare_amount", "Vendor")

    assert not result.succeeded
    assert result.metrics == {}
    assert result.params == {"column": "fare_amount", "group_by": "Vendor"}
    assert result.error == "Column 'Vendor' does not exist for groupby"


def test_breakdown_by_supports_non_positive_and_null_conditions(spark: SparkSession) -> None:
    df = spark.createDataFrame(
        [(1, 0.0), (1, -1.0), (2, 5.0), (2, None), (2, None)],
        SCHEMA,
    )

    non_positive = breakdown_by(df, "fare_amount", "VendorID", "non_positive")
    nulls = breakdown_by(df, "fare_amount", "VendorID", "null")

    assert non_positive.metrics == {"VendorID=1": 2.0}
    assert non_positive.params["condition"] == "non_positive"
    assert nulls.metrics == {"VendorID=2": 2.0}


def test_breakdown_by_keeps_only_largest_groups(spark: SparkSession) -> None:
    rows = [(group, -1.0) for group in range(40) for _ in range(group + 1)]
    df = spark.createDataFrame(rows, SCHEMA)

    result = breakdown_by(df, "fare_amount", "VendorID")

    assert len(result.metrics) == 25
    assert result.metrics["VendorID=39"] == 40.0
    assert "VendorID=0" not in result.metrics
