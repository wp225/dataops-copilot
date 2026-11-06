"""Tests for local and ADLS report stores."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dataops_copilot.agent.services.report_store import (
    AdlsReportStore,
    LocalJsonReportStore,
    report_blob_name,
)
from tests.factories import make_completed_investigation


def test_local_store_returns_empty_when_file_missing(tmp_path: Path) -> None:
    assert LocalJsonReportStore(tmp_path / "missing.json").load_reports() == []


def test_local_store_round_trips_and_filters_by_metric(tmp_path: Path) -> None:
    store = LocalJsonReportStore(tmp_path / "nested" / "reports.json")
    fares = make_completed_investigation("negative_fare_rate")
    dupes = make_completed_investigation("duplicate_rate", None)

    store.save_report(fares)
    store.save_report(dupes)

    assert store.load_reports() == [fares, dupes]
    assert store.load_reports(metric="duplicate_rate") == [dupes]


@dataclass
class FakeBlob:
    name: str


@dataclass
class FakeDownload:
    payload: bytes

    def readall(self) -> bytes:
        return self.payload


@dataclass
class FakeContainer:
    blobs: dict[str, bytes] = field(default_factory=dict)

    def upload_blob(self, name: str, data: bytes, **_: Any) -> None:
        self.blobs[name] = data

    def list_blobs(self, name_starts_with: str) -> list[FakeBlob]:
        return [FakeBlob(name) for name in self.blobs if name.startswith(name_starts_with)]

    def download_blob(self, name: str) -> FakeDownload:
        return FakeDownload(self.blobs[name])


def test_adls_store_partitions_blobs_by_metric() -> None:
    container = FakeContainer()
    store = AdlsReportStore(container)  # ty: ignore[invalid-argument-type]
    fares = make_completed_investigation("negative_fare_rate")
    dupes = make_completed_investigation("duplicate_rate", None)

    written = store.save_report(fares)
    store.save_report(dupes)

    assert written == report_blob_name(fares)
    assert written.startswith("rca-reports/negative_fare_rate/yellow-taxi/batch-001/")
    assert store.load_reports(metric="negative_fare_rate") == [fares]
    assert len(store.load_reports()) == 2
