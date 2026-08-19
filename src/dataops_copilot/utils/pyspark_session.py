from pyspark.sql import SparkSession


def spark_session(app_name: str) -> SparkSession:
    """Return a local Spark Session."""
    return SparkSession.builder.master("local[2]").appName(app_name).getOrCreate()
