"""HTTP API for DataOps Copilot."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI

from dataops_copilot.agent.models import IncidentInvestigationRequest, IncidentRCAReport
from dataops_copilot.agent.service import (
    InvestigationService,
    ScanRequest,
    ScanResult,
    build_service,
)
from dataops_copilot.config import get_settings

app = FastAPI(
    title="DataOps Copilot",
    description="Agentic data-quality and incident-response system for Azure data platforms.",
    version="0.1.0",
)


@lru_cache
def get_service() -> InvestigationService:
    """Build the investigation service once, on first use."""
    return build_service(get_settings())


Service = Annotated[InvestigationService, Depends(get_service)]


@app.get("/healthz", tags=["system"])
def healthz() -> dict[str, str]:
    """Return the service health status."""
    return {"status": "ok"}


@app.post("/investigations", tags=["rca"])
def investigate(request: IncidentInvestigationRequest, service: Service) -> IncidentRCAReport:
    """Investigate one known incident and return its RCA report."""
    return service.investigate(request)


@app.post("/scans", tags=["quality"])
def scan(request: ScanRequest, service: Service) -> ScanResult:
    """Profile a batch, detect incidents and investigate each one."""
    return service.scan(request)
