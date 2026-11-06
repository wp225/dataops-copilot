"""Persistence for completed RCA reports: a local JSON file or ADLS Gen2."""

import json
from pathlib import Path
from typing import Protocol

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient

from dataops_copilot.agent.models import IncidentRCAReport

REPORT_PREFIX = "rca-reports"


class ReportStore(Protocol):
    """Load and save completed RCA reports."""

    def load_reports(self, metric: str | None = None) -> list[IncidentRCAReport]:
        """Return stored reports, optionally only those for one incident metric."""
        ...

    def save_report(self, report: IncidentRCAReport) -> str:
        """Persist one report and return where it was written."""
        ...


class LocalJsonReportStore:
    """Store all reports as a JSON list in one local file."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load_reports(self, metric: str | None = None) -> list[IncidentRCAReport]:
        """Return stored reports; a missing file means no history yet."""
        if not self.path.exists():
            return []
        raw_reports = json.loads(self.path.read_text(encoding="utf-8"))
        reports = [IncidentRCAReport.model_validate(raw) for raw in raw_reports]
        if metric is None:
            return reports
        return [report for report in reports if report.request.incident.metric == metric]

    def save_report(self, report: IncidentRCAReport) -> str:
        """Append the report to the JSON file."""
        reports = self.load_reports()
        reports.append(report)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([item.model_dump(mode="json") for item in reports], indent=2),
            encoding="utf-8",
        )
        return str(self.path)


def report_blob_name(report: IncidentRCAReport) -> str:
    """Return the blob path for a report, partitioned by metric for cheap lookups."""
    request = report.request
    timestamp = report.completed_at.strftime("%Y%m%dT%H%M%S%fZ")
    return (
        f"{REPORT_PREFIX}/{request.incident.metric}/{request.dataset_name}/"
        f"{request.batch_id}/{timestamp}.json"
    )


class AdlsReportStore:
    """Store one JSON blob per report in an ADLS Gen2 (blob) container."""

    def __init__(self, container: ContainerClient) -> None:
        self.container = container

    @classmethod
    def from_account(cls, account_url: str, container_name: str) -> "AdlsReportStore":
        """Connect with DefaultAzureCredential (managed identity in Azure, az login locally)."""
        service = BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential())
        return cls(service.get_container_client(container_name))

    def load_reports(self, metric: str | None = None) -> list[IncidentRCAReport]:
        """Download every report blob under the (metric) prefix."""
        prefix = f"{REPORT_PREFIX}/{metric}/" if metric else f"{REPORT_PREFIX}/"
        reports: list[IncidentRCAReport] = []
        for blob in self.container.list_blobs(name_starts_with=prefix):
            payload = self.container.download_blob(blob.name).readall()
            reports.append(IncidentRCAReport.model_validate_json(payload))
        return reports

    def save_report(self, report: IncidentRCAReport) -> str:
        """Upload the report as a new blob."""
        blob_name = report_blob_name(report)
        self.container.upload_blob(
            blob_name,
            report.model_dump_json(indent=2).encode("utf-8"),
            overwrite=True,
        )
        return blob_name
