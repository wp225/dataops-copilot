"""Tests for the run_checks node (JVM-free: check execution is stubbed)."""

import pytest

from dataops_copilot.agent.checks.models import CheckResult, PlannedCheck
from dataops_copilot.agent.nodes import run_checks as run_checks_module
from dataops_copilot.agent.nodes.run_checks import make_run_checks_node
from dataops_copilot.agent.state import InvestigationState
from tests.factories import make_plan, make_request

BATCH = object()


@pytest.fixture(autouse=True)
def fake_run_check(monkeypatch: pytest.MonkeyPatch) -> list[PlannedCheck]:
    executed: list[PlannedCheck] = []

    def run_check(df: object, planned: PlannedCheck) -> CheckResult:
        assert df is BATCH
        executed.append(planned)
        params = {
            key: value
            for key, value in planned.model_dump(
                include={"column", "group_by", "condition"}
            ).items()
            if value is not None
        }
        return CheckResult(
            check_name=planned.check_name, params=params, metrics={"n": 1.0}, succeeded=True
        )

    monkeypatch.setattr(run_checks_module, "run_check", run_check)
    return executed


def test_run_checks_executes_plan_against_loaded_batch(
    fake_run_check: list[PlannedCheck],
) -> None:
    loaded: list[str] = []

    def load(uri: str) -> object:
        loaded.append(uri)
        return BATCH

    state = InvestigationState(
        request=make_request(data_uri="data/batch.parquet"), analysis_plan=make_plan()
    )

    update = make_run_checks_node(load)(state)  # ty: ignore[invalid-argument-type]

    assert loaded == ["data/batch.parquet"]
    assert [check.check_name for check in fake_run_check] == ["breakdown_by"]
    assert update["check_results"][0].succeeded


def test_run_checks_skips_checks_that_already_succeeded(
    fake_run_check: list[PlannedCheck],
) -> None:
    node = make_run_checks_node(lambda _: BATCH)  # ty: ignore[invalid-argument-type]
    first = InvestigationState(request=make_request(data_uri="x"), analysis_plan=make_plan())
    previous = node(first)["check_results"]

    replanned = make_plan(
        PlannedCheck(
            check_name="breakdown_by",
            column="fare_amount",
            group_by="payment_type",
            condition="negative",
            reason="same check, explicit default condition",
        ),
        PlannedCheck(check_name="value_range", column="fare_amount", reason="new"),
    )
    second = first.model_copy(update={"analysis_plan": replanned, "check_results": previous})

    results = node(second)["check_results"]

    assert [result.check_name for result in results] == ["breakdown_by", "value_range"]
    assert len(fake_run_check) == 2
    assert node(second.model_copy(update={"check_results": results})) == {}


def test_run_checks_records_failure_when_request_has_no_data_uri() -> None:
    node = make_run_checks_node(lambda _: BATCH)  # ty: ignore[invalid-argument-type]

    update = node(InvestigationState(request=make_request(), analysis_plan=make_plan()))

    [result] = update["check_results"]
    assert not result.succeeded
    assert result.error == "Could not load batch data: ValueError: the request has no data_uri"


def test_run_checks_without_plan_is_a_no_op() -> None:
    def never(_: str) -> object:
        raise AssertionError

    node = make_run_checks_node(never)  # ty: ignore[invalid-argument-type]

    assert node(InvestigationState(request=make_request())) == {}
