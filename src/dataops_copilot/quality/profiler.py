from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from dataops_copilot.quality.models import QualityReport

# spark = SparkSession.builder.master('local[2]').appName('DataOps').getOrCreate()


def read_parquet(file_path: str, spark_session: SparkSession) -> DataFrame:
    """Return a lazily evaluated DataFrame from a Parquet path."""
    return spark_session.read.parquet(file_path)


def calculate_metrics(df: DataFrame) -> QualityReport:
    """Return the metrics as dict."""
    core_metrics = [
        F.count(F.lit(1)).alias("row_count"),
        F.coalesce(F.avg((F.col("fare_amount") < 0).cast("double")), F.lit(0.0)).alias(
            "negative_fare_rate"
        ),
        F.coalesce(F.avg((F.col("trip_distance") <= 0).cast("double")), F.lit(0.0)).alias(
            "invalid_trip_distance_rate"
        ),
    ]

    null_rate_aliases = {
        column_name: f"{column_name}_null_rate" for _, column_name in enumerate(df.columns)
    }

    null_rate_metrics = [
        F.coalesce(F.avg(F.col(column_name).isNull().cast("double")), F.lit(0.0)).alias(alias)
        for column_name, alias in null_rate_aliases.items()
    ]
    summary_row = df.agg(*(core_metrics + null_rate_metrics)).first()
    if summary_row is None:
        message = "Spark aggregation unexpectedly returned no metrics row."
        raise RuntimeError(message)

    metrics_summary = summary_row.asDict()
    row_count = metrics_summary["row_count"]
    if row_count > 0:
        distinct_count = df.distinct().count()
        duplicate_rate = (row_count - distinct_count) / row_count
    else:
        duplicate_rate = 0.0

    null_rates = {c: metrics_summary[f"{c}_null_rate"] for c in df.columns}
    return QualityReport(
        row_count=row_count,
        negative_fare_rate=metrics_summary["negative_fare_rate"],
        invalid_trip_distance_rate=metrics_summary["invalid_trip_distance_rate"],
        duplicate_rate=duplicate_rate,
        null_rates=null_rates,
    )


if __name__ == "__main__":
    from pathlib import Path

    from dataops_copilot.utils import pyspark_session

    session = pyspark_session.spark_session(app_name="dataops-copilot-test")
    df = read_parquet("data/yellow_tripdata_2026-01.parquet", session)
