"""Test for spark profiler."""

import pytest
from pyspark.sql import SparkSession

from dataops_copilot.quality.profiler import calculate_metrics


def test_calculate_metrics_reports_expected_quality_values(spark: SparkSession) -> None:
    dataframe = spark.createDataFrame(
        [
            (10.0, 2.5, 1),
            (-5.0, 0.0, None),
            (-5.0, 0.0, None),
            (20.0, 4.0, 2),
        ],
        ["fare_amount", "trip_distance", "VendorID"],
    )

    report = calculate_metrics(dataframe)

    assert report.row_count == 4
    assert report.duplicate_rate == pytest.approx(0.25)
    assert report.negative_fare_rate == pytest.approx(0.5)
    assert report.invalid_trip_distance_rate == pytest.approx(0.5)
    assert report.null_rates["VendorID"] == pytest.approx(0.5)
    assert report.null_rates["fare_amount"] == pytest.approx(0.0)
