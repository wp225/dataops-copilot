"""Shared builders for valid domain objects used across tests."""

from dataops_copilot.agent.checks.models import PlannedCheck
from dataops_copilot.agent.models import (
    AnalysisHypothesis,
    AnalysisPlan,
    EvidenceAssessment,
    IncidentInvestigationRequest,
    IncidentRCAReport,
    RCAReport,
)
from dataops_copilot.quality.models import DataQualityIncident, QualityReport


def make_request(
    metric: str = "negative_fare_rate",
    affected_column: str | None = "fare_amount",
    dataset_name: str = "yellow-taxi",
    data_uri: str | None = None,
) -> IncidentInvestigationRequest:
    """Create a small valid investigation request."""
    return IncidentInvestigationRequest(
        incident=DataQualityIncident(
            metric=metric,
            observed_rate=0.01,
            threshold=0.001,
            affected_column=affected_column,
        ),
        quality_report=QualityReport(
            row_count=100,
            negative_fare_rate=0.01,
            invalid_trip_distance_rate=0.0,
            duplicate_rate=0.0,
            null_rates={"fare_amount": 0.0, "payment_type": 0.0},
        ),
        dataset_name=dataset_name,
        batch_id="batch-001",
        data_uri=data_uri,
    )


def make_rca_report(**overrides: object) -> RCAReport:
    """Create a valid RCA report."""
    fields: dict[str, object] = {
        "likely_cause": "Test cause",
        "confidence": "medium",
        "explanation": "Test explanation",
        "previous_similar_incidents": 0,
        "evidence": ["Test evidence"],
        "analyses_executed": ["Test analysis"],
        "escalation_required": False,
        "recommendations": ["Test recommendation"],
    }
    fields.update(overrides)
    return RCAReport.model_validate(fields)


def make_completed_investigation(
    metric: str = "negative_fare_rate",
    affected_column: str | None = "fare_amount",
    dataset_name: str = "yellow-taxi",
) -> IncidentRCAReport:
    """Create a past RCA record."""
    return IncidentRCAReport(
        request=make_request(metric, affected_column, dataset_name),
        report=make_rca_report(),
    )


def make_plan(*checks: PlannedCheck) -> AnalysisPlan:
    """Create a one-hypothesis plan running the given checks."""
    planned = list(checks) or [
        PlannedCheck(
            check_name="breakdown_by",
            column="fare_amount",
            group_by="payment_type",
            reason="Refunds would concentrate in one payment type.",
        )
    ]
    return AnalysisPlan(
        analysis_goal="Identify the source of negative fares.",
        hypotheses=[
            AnalysisHypothesis(
                likely_cause="Refund values were mapped into fare_amount.",
                rationale="The negative-fare rate exceeds the policy threshold.",
                likelihood="medium",
                checks_to_run=planned,
            )
        ],
    )


def make_assessment(
    *, sufficient: bool, open_questions: list[str] | None = None
) -> EvidenceAssessment:
    """Create an evidence assessment."""
    return EvidenceAssessment(
        evidence_sufficient=sufficient,
        supported_cause="Refunds mapped into fare_amount" if sufficient else None,
        confidence="high" if sufficient else "low",
        reasoning="Test reasoning",
        open_questions=open_questions or [],
    )
