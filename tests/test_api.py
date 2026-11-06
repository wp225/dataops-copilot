"""Tests for the HTTP API."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from dataops_copilot.agent.models import IncidentInvestigationRequest, IncidentRCAReport
from dataops_copilot.agent.service import ScanRequest, ScanResult
from dataops_copilot.api import app, get_service
from dataops_copilot.quality.models import QualityReport
from tests.factories import make_rca_report, make_request


class FakeService:
    def investigate(self, request: IncidentInvestigationRequest) -> IncidentRCAReport:
        return IncidentRCAReport(request=request, report=make_rca_report())

    def scan(self, request: ScanRequest) -> ScanResult:
        return ScanResult(
            dataset_name=request.dataset_name,
            batch_id=request.batch_id,
            quality_report=QualityReport(
                row_count=0,
                null_rates={},
                duplicate_rate=0.0,
                negative_fare_rate=0.0,
                invalid_trip_distance_rate=0.0,
            ),
            incidents=[],
        )


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_service] = FakeService
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_healthz_returns_ok(client: TestClient) -> None:
    """The health endpoint reports a healthy service."""
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_investigations_returns_rca_report(client: TestClient) -> None:
    response = client.post("/investigations", json=make_request().model_dump(mode="json"))

    assert response.status_code == 200
    assert response.json()["report"]["likely_cause"] == "Test cause"


def test_scans_returns_scan_result(client: TestClient) -> None:
    response = client.post("/scans", json={"dataset_name": "d", "batch_id": "b", "data_uri": "u"})

    assert response.status_code == 200
    assert response.json()["incidents"] == []


def test_investigations_rejects_invalid_body(client: TestClient) -> None:
    assert client.post("/investigations", json={"dataset_name": "d"}).status_code == 422
