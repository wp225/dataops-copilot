"""Tests for deterministic quality-incident detection."""

from dataops_copilot.quality.detector import detect_incidents
from dataops_copilot.quality.models import QualityReport
from dataops_copilot.quality.policy import QualityPolicy


def test_detect_incidents_returns_all_policy_violations() -> None:
    """Flag every metric whose rate exceeds the configured threshold."""
    report = QualityReport(
        row_count=100,
        null_rates={
            "VendorID": 0.002,
            "fare_amount": 0.0,
            "trip_distance": 0.0,
        },
        duplicate_rate=0.002,
        negative_fare_rate=0.002,
        invalid_trip_distance_rate=0.002,
    )
    policy = QualityPolicy(threshold_rate=0.001)

    incidents = detect_incidents(report, policy)

    assert len(incidents) == 4
    assert {(incident.metric, incident.affected_column) for incident in incidents} == {
        ("null_rate", "VendorID"),
        ("duplicate_rate", None),
        ("negative_fare_rate", "fare_amount"),
        ("invalid_trip_distance_rate", "trip_distance"),
    }
    assert all(incident.observed_rate == 0.002 for incident in incidents)
    assert all(incident.threshold == 0.001 for incident in incidents)


def test_detect_incidents_does_not_flag_rate_at_threshold() -> None:
    """Do not flag a value equal to the strict greater-than threshold."""
    report = QualityReport(
        row_count=100,
        null_rates={"VendorID": 0.001},
        duplicate_rate=0.001,
        negative_fare_rate=0.001,
        invalid_trip_distance_rate=0.001,
    )
    policy = QualityPolicy(threshold_rate=0.001)

    incidents = detect_incidents(report, policy)

    assert incidents == []
