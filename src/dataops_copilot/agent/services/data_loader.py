"""Load a batch's Parquet data from a local path or ADLS Gen2 into Spark.

Remote data is downloaded with DefaultAzureCredential and read locally, which
keeps the container free of Hadoop-Azure jars and storage keys.
"""

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from pyspark.sql import DataFrame, SparkSession

DataLoader = Callable[[str], DataFrame]


@dataclass(frozen=True)
class BlobLocation:
    """A blob path split into its account URL, container and object path."""

    account_url: str
    container: str
    path: str


def parse_remote_uri(uri: str) -> BlobLocation | None:
    """Parse abfss:// or https:// storage URIs. Returns None for local paths.

    abfss://<container>@<account>.dfs.core.windows.net/<path>
    https://<account>.blob.core.windows.net/<container>/<path>
    """
    parsed = urlparse(uri)
    if parsed.scheme in {"abfss", "abfs"}:
        container, _, host = parsed.netloc.partition("@")
        account = host.split(".", 1)[0]
        return BlobLocation(
            account_url=f"https://{account}.blob.core.windows.net",
            container=container,
            path=parsed.path.lstrip("/"),
        )
    if parsed.scheme == "https":
        account = parsed.netloc.split(".", 1)[0]
        container, _, path = parsed.path.lstrip("/").partition("/")
        return BlobLocation(
            account_url=f"https://{account}.blob.core.windows.net",
            container=container,
            path=path,
        )
    return None


def download_parquet(location: BlobLocation, cache_dir: Path) -> Path:
    """Download one Parquet blob, or every .parquet blob under a prefix."""
    digest = hashlib.sha256(
        f"{location.account_url}/{location.container}/{location.path}".encode()
    ).hexdigest()[:16]
    target = cache_dir / digest
    if target.exists():
        return target

    service = BlobServiceClient(location.account_url, credential=DefaultAzureCredential())
    container = service.get_container_client(location.container)
    blob_names = [
        blob.name
        for blob in container.list_blobs(name_starts_with=location.path)
        if blob.name == location.path or blob.name.endswith(".parquet")
    ]
    if not blob_names:
        raise FileNotFoundError(f"No Parquet data found at {location}")

    staging = cache_dir / f"{digest}.partial"
    staging.mkdir(parents=True, exist_ok=True)
    for index, name in enumerate(blob_names):
        local_file = staging / f"part-{index:05d}.parquet"
        local_file.write_bytes(container.download_blob(name).readall())
    staging.rename(target)
    return target


def load_parquet(spark: SparkSession, uri: str, cache_dir: Path) -> DataFrame:
    """Read Parquet from a local path or a remote ADLS URI."""
    location = parse_remote_uri(uri)
    local_path = Path(uri) if location is None else download_parquet(location, cache_dir)
    return spark.read.parquet(str(local_path))


def make_parquet_loader(spark: SparkSession, cache_dir: Path | str) -> DataLoader:
    """Create a loader that reads Parquet from a local path or ADLS URI."""
    cache_path = Path(cache_dir)

    def load(uri: str) -> DataFrame:
        return load_parquet(spark, uri, cache_path)

    return load
