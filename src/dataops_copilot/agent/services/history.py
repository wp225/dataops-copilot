"""Search and Load Previous Similar Cases."""

from collections.abc import Iterable

from dataops_copilot.agent.models import (
    HistoricalIncidentMatch,
    IncidentInvestigationRequest,
    IncidentRCAReport,
)


def search_rca_reports(
    investigation_request: IncidentInvestigationRequest,
    reports: Iterable[IncidentRCAReport],
) -> list[HistoricalIncidentMatch]:
    """Return past reports for the same metric. Syntactic for now, RAG later.

    Matches that also share the affected column or dataset are ranked first.
    """
    current_incident = investigation_request.incident
    matches: list[HistoricalIncidentMatch] = []

    for historical_report in reports:
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

    matches.sort(key=lambda match: len(match.similarity_reasons), reverse=True)
    return matches
