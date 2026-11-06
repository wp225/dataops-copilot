"""Tests for the end-to-end investigation service."""

from pathlib import Path
from typing import Any

import pytest

from dataops_copilot.agent import service as service_module
from dataops_copilot.agent.models import IncidentInvestigationRequest, IncidentRCAReport
from dataops_copilot.agent.service import (
    InvestigationService,
    ScanRequest,
    build_report_store,
)
from dataops_copilot.agent.services.report_store import LocalJsonReportStore
from dataops_copilot.config import Settings
from dataops_copilot.quality.models import QualityReport
from tests.factories import make_rca_report, make_request


class FakeGraph:
    def __init__(self) -> None:
        self.requests: list[IncidentInvestigationRequest] = []

    def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = payload["request"]
        self.requests.append(request)
        return {"final_result": IncidentRCAReport(request=request, report=make_rca_report())}


BATCH = object()


@pytest.fixture(autouse=True)
def fake_profiler(monkeypatch: pytest.MonkeyPatch) -> None:
    def calculate_metrics(df: object) -> QualityReport:
        assert df is BATCH
        return QualityReport(
            row_count=4,
            null_rates={"fare_amount": 0.0},
            duplicate_rate=0.0,
            negative_fare_rate=0.25,
            invalid_trip_distance_rate=0.25,
        )

    monkeypatch.setattr(service_module, "calculate_metrics", calculate_metrics)


def _service(tmp_path: Path, graph: object) -> InvestigationService:
    return InvestigationService(
        graph=graph,  # ty: ignore[invalid-argument-type]
        store=LocalJsonReportStore(tmp_path / "reports.json"),
        load_data=lambda _: BATCH,  # ty: ignore[invalid-argument-type]
    )


def test_investigate_persists_the_report(tmp_path: Path) -> None:
    service = _service(tmp_path, FakeGraph())

    report = service.investigate(make_request())

    assert service.store.load_reports() == [report]


def test_investigate_fails_when_graph_returns_no_report(tmp_path: Path) -> None:
    class EmptyGraph:
        def invoke(self, _: object) -> dict[str, Any]:
            return {}

    with pytest.raises(RuntimeError, match="without a report"):
        _service(tmp_path, EmptyGraph()).investigate(make_request())


def test_scan_profiles_detects_and_investigates_each_incident(tmp_path: Path) -> None:
    graph = FakeGraph()
    service = _service(tmp_path, graph)

    result = service.scan(
        ScanRequest(dataset_name="yellow-taxi", batch_id="b1", data_uri="batch.parquet")
    )

    metrics = sorted(incident.metric for incident in result.incidents)
    assert metrics == ["invalid_trip_distance_rate", "negative_fare_rate"]
    assert len(result.reports) == 2
    assert {request.data_uri for request in graph.requests} == {"batch.parquet"}
    assert result.quality_report.row_count == 4


def test_scan_can_skip_investigation(tmp_path: Path) -> None:
    graph = FakeGraph()

    result = _service(tmp_path, graph).scan(
        ScanRequest(dataset_name="d", batch_id="b", data_uri="u", investigate=False)
    )

    assert result.incidents
    assert result.reports == []
    assert graph.requests == []


def test_build_report_store_requires_account_for_adls() -> None:
    with pytest.raises(ValueError, match="DATAOPS_ADLS_ACCOUNT_URL"):
        build_report_store(Settings(report_store="adls", adls_account_url=None))


def test_build_report_store_defaults_to_local(tmp_path: Path) -> None:
    store = build_report_store(Settings(local_report_path=tmp_path / "r.json"))

    assert isinstance(store, LocalJsonReportStore)
