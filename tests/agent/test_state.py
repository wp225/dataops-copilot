"""Tests for the shared investigation state model."""

from dataops_copilot.agent.state import InvestigationState
from tests.factories import make_assessment, make_request


def test_investigation_state_defaults() -> None:
    """A fresh state carries only the request, with empty defaults."""
    state = InvestigationState(request=make_request())

    assert state.historical_matches == []
    assert state.analysis_plan is None
    assert state.check_results == []
    assert state.assessment is None
    assert state.evidence_sufficient is False
    assert state.iteration_count == 0
    assert state.final_result is None


def test_evidence_sufficient_follows_latest_assessment() -> None:
    state = InvestigationState(request=make_request(), assessment=make_assessment(sufficient=True))

    assert state.evidence_sufficient is True
    assert state.to_context().assessment == state.assessment
