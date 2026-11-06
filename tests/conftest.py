from collections.abc import Iterator

import pytest
from pyspark.sql import SparkSession

from dataops_copilot.utils.pyspark_session import spark_session


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark every test that needs a JVM (uses the spark fixture) with `spark`."""
    for item in items:
        if "spark" in getattr(item, "fixturenames", ()):
            item.add_marker(pytest.mark.spark)


@pytest.fixture(scope="session")
def spark() -> Iterator[SparkSession]:
    """Local spark session for test suit."""
    spark = spark_session("dataops-copilot-tests")

    spark.sparkContext.setLogLevel("ERROR")

    yield spark

    spark.stop()
