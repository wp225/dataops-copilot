"""Search and Load Previous Similar Cases."""

import json
from pathlib import Path

from dataops_copilot.agent.models import (
    HistoricalIncidentMatch,
    IncidentInvestigationRequest,
    IncidentRCAReport,
)


def search_rca_reports(
    investigation_request: IncidentInvestigationRequest, rca_dump_path: Path | str
) -> list[HistoricalIncidentMatch]:
    """Searches for similar incidents from json dump. Syntatic for now, RAG later."""
    current_incident = investigation_request.incident

    raw_reports = json.loads(Path(rca_dump_path).read_text(encoding="utf-8"))

    matches: list[HistoricalIncidentMatch] = []

    for raw_report in raw_reports:
        historical_report: IncidentRCAReport = IncidentRCAReport.model_validate(raw_report)
        historic_incident = historical_report.request.incident
        if historic_incident.metric != current_incident.metric:
            continue

        similarity_reasons = [f"same metric: {current_incident.metric}"]

        if (
            current_incident.affected_column is not None
            and historic_incident.affected_column == current_incident.affected_column
        ):
            similarity_reasons.append(f"same affected column: {current_incident.affected_column}")

        if historical_report.request.dataset_name == investigation_request.dataset_name:
            similarity_reasons.append(f"same dataset: {investigation_request.dataset_name}")

        matches.append(
            HistoricalIncidentMatch(
                historical_incident=historical_report,
                similarity_reasons=similarity_reasons,
            )
        )

    return matches
