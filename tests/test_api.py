"""Tests for the HTTP API."""

from fastapi.testclient import TestClient

from dataops_copilot.api import app

client = TestClient(app)


def test_healthz_returns_ok() -> None:
    """The health endpoint reports a healthy service."""
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
