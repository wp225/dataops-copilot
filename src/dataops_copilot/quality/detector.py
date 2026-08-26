from dataops_copilot.quality.models import DataQualityIncident, QualityReport
from dataops_copilot.quality.policy import QualityPolicy


def detect_incidents(
    report: QualityReport,
    policy: QualityPolicy,
) -> list[DataQualityIncident]:
    """Return all quality-policy violations in a report."""
    incidents: list[DataQualityIncident] = []

    for column_name, null_rate in report.null_rates.items():
        if null_rate > policy.threshold_rate:
            incidents.append(
                DataQualityIncident(
                    metric="null_rate",
                    observed_rate=null_rate,
                    threshold=policy.threshold_rate,
                    affected_column=column_name,
                )
            )

    if report.duplicate_rate > policy.threshold_rate:
        incidents.append(
            DataQualityIncident(
                metric="duplicate_rate",
                observed_rate=report.duplicate_rate,
                threshold=policy.threshold_rate,
                affected_column=None,
            )
        )
    if report.negative_fare_rate > policy.threshold_rate:
        incidents.append(
            DataQualityIncident(
                metric="negative_fare_rate",
                observed_rate=report.negative_fare_rate,
                threshold=policy.threshold_rate,
                affected_column="fare_amount",
            )
        )
    if report.invalid_trip_distance_rate > policy.threshold_rate:
        incidents.append(
            DataQualityIncident(
                metric="invalid_trip_distance_rate",
                observed_rate=report.invalid_trip_distance_rate,
                threshold=policy.threshold_rate,
                affected_column="trip_distance",
            )
        )

    return incidents
