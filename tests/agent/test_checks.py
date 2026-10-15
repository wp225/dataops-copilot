from pyspark.sql import SparkSession

from dataops_copilot.agent.checks.value_range import value_range


def test_value_range_reports_min_max_negatives_and_nulls(spark: SparkSession) -> None:
    df = spark.createDataFrame(
        [(10.0,), (-5.0,), (25.5,), (-1.0,), (None,)],
        "fare_amount double",
    )

    result = value_range(df, "fare_amount")

    assert result.succeeded
    assert result.check_name == "value_range"
    assert result.metrics == {
        "row_count": 5.0,
        "min": -5.0,
        "max": 25.5,
        "null_count": 1.0,
        "negative_count": 2.0,
    }
    assert result.params == {"column": "fare_amount"}


def test_value_range_handles_empty_dataframe(spark: SparkSession) -> None:
    df = spark.createDataFrame([], "fare_amount double")

    result = value_range(df, "fare_amount")

    assert result.succeeded
    assert result.metrics == {"row_count": 0.0, "null_count": 0.0, "negative_count": 0.0}


def test_value_range_fails_for_missing_column(spark: SparkSession) -> None:
    df = spark.createDataFrame([(1.0,)], "fare_amount double")

    result = value_range(df, "tip_amount")

    assert not result.succeeded
    assert result.metrics == {}
    assert result.error == "Column 'tip_amount' does not exist."
