from collections.abc import Iterator

import pytest
from pyspark.sql import SparkSession

from dataops_copilot.utils.pyspark_session import spark_session


@pytest.fixture(scope="session")
def spark() -> Iterator[SparkSession]:
    """Local spark session for test suit."""
    spark = spark_session("dataops-copilot-tests")

    spark.sparkContext.setLogLevel("ERROR")

    yield spark

    spark.stop()
