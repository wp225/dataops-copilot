"""Tests for batch data loading."""

from pathlib import Path

import pytest
from pyspark.sql import SparkSession

from dataops_copilot.agent.services import data_loader
from dataops_copilot.agent.services.data_loader import (
    BlobLocation,
    download_parquet,
    make_parquet_loader,
    parse_remote_uri,
)


def test_parse_abfss_uri() -> None:
    assert parse_remote_uri(
        "abfss://raw@stdataops.dfs.core.windows.net/yellow/2026-01.parquet"
    ) == BlobLocation(
        account_url="https://stdataops.blob.core.windows.net",
        container="raw",
        path="yellow/2026-01.parquet",
    )


def test_parse_https_blob_uri() -> None:
    assert parse_remote_uri(
        "https://stdataops.blob.core.windows.net/raw/yellow/2026-01.parquet"
    ) == BlobLocation(
        account_url="https://stdataops.blob.core.windows.net",
        container="raw",
        path="yellow/2026-01.parquet",
    )


def test_local_paths_are_not_remote() -> None:
    assert parse_remote_uri("data/yellow.parquet") is None
    assert parse_remote_uri("/abs/data/yellow.parquet") is None


def test_loader_reads_local_parquet(tmp_path: Path, spark: SparkSession) -> None:
    target = tmp_path / "batch.parquet"
    spark.createDataFrame([(1.0,), (-2.0,)], "fare_amount double").write.parquet(str(target))

    df = make_parquet_loader(spark, tmp_path / "cache")(str(target))

    assert df.count() == 2


class FakeBlob:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeContainer:
    def __init__(self, blobs: dict[str, bytes]) -> None:
        self.blobs = blobs
        self.downloads: list[str] = []

    def list_blobs(self, name_starts_with: str) -> list[FakeBlob]:
        return [FakeBlob(name) for name in self.blobs if name.startswith(name_starts_with)]

    def download_blob(self, name: str) -> "FakeContainer":
        self.downloads.append(name)
        self._current = name
        return self

    def readall(self) -> bytes:
        return self.blobs[self._current]


@pytest.fixture
def fake_container(monkeypatch: pytest.MonkeyPatch) -> FakeContainer:
    container = FakeContainer(
        {
            "yellow/2026-01/part-0.parquet": b"a",
            "yellow/2026-01/part-1.parquet": b"b",
            "yellow/2026-01/_SUCCESS": b"",
        }
    )

    class FakeService:
        def __init__(self, account_url: str, credential: object) -> None:  # noqa: ARG002
            assert account_url == "https://acct.blob.core.windows.net"

        def get_container_client(self, name: str) -> FakeContainer:
            assert name == "raw"
            return container

    monkeypatch.setattr(data_loader, "BlobServiceClient", FakeService)
    monkeypatch.setattr(data_loader, "DefaultAzureCredential", lambda: None)
    return container


def test_download_parquet_fetches_prefix_once(
    tmp_path: Path, fake_container: FakeContainer
) -> None:
    location = BlobLocation("https://acct.blob.core.windows.net", "raw", "yellow/2026-01")

    target = download_parquet(location, tmp_path)
    again = download_parquet(location, tmp_path)

    assert target == again
    assert sorted(path.read_bytes() for path in target.iterdir()) == [b"a", b"b"]
    assert len(fake_container.downloads) == 2


def test_download_parquet_raises_when_nothing_matches(
    tmp_path: Path, fake_container: FakeContainer
) -> None:
    location = BlobLocation("https://acct.blob.core.windows.net", "raw", "missing/")

    with pytest.raises(FileNotFoundError):
        download_parquet(location, tmp_path)


def test_loader_routes_remote_uris_through_download(
    tmp_path: Path, fake_container: FakeContainer
) -> None:
    class FakeReader:
        def parquet(self, path: str) -> str:
            return path

    class FakeSpark:
        read = FakeReader()

    load = make_parquet_loader(FakeSpark(), tmp_path)  # ty: ignore[invalid-argument-type]

    path = load("abfss://raw@acct.dfs.core.windows.net/yellow/2026-01")

    assert path.startswith(str(tmp_path))
    assert load("data/local.parquet") == "data/local.parquet"
