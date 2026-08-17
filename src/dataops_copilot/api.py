"""HTTP API for DataOps Copilot."""

from fastapi import FastAPI

app = FastAPI(
    title="DataOps Copilot",
    description="Agentic data-quality and incident-response system for Azure data platforms.",
    version="0.1.0",
)


@app.get("/healthz", tags=["system"])
def healthz() -> dict[str, str]:
    """Return the service health status."""
    return {"status": "ok"}
