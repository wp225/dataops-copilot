"""Integration tests for the RCA LangGraph investigation loop."""

from pathlib import Path

import pytest

from dataops_copilot.agent.checks.models import CheckResult, PlannedCheck
from dataops_copilot.agent.graph import InvestigationDependencies, build_investigation_graph
from dataops_copilot.agent.models import (
    AnalysisPlan,
    EvidenceAssessment,
    InvestigationContext,
    PlanningContext,
    RCAReport,
)
from dataops_copilot.agent.nodes import run_checks as run_checks_module
from dataops_copilot.agent.services.report_store import LocalJsonReportStore
from tests.factories import (
    make_assessment,
    make_completed_investigation,
    make_plan,
    make_rca_report,
    make_request,
)

BATCH = object()


@pytest.fixture(autouse=True)
def fake_run_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stand in for Spark: return canned metrics for each planned check."""

    def run_check(df: object, planned: PlannedCheck) -> CheckResult:
        assert df is BATCH
        if planned.check_name == "breakdown_by":
            return CheckResult(
                check_name="breakdown_by",
                params={"column": "fare_amount", "group_by": "payment_type"},
                metrics={"payment_type=4": 2.0},
                succeeded=True,
            )
        return CheckResult(
            check_name=planned.check_name,
            params={"column": planned.column or ""},
            metrics={"min": -5.0},
            succeeded=True,
        )

    monkeypatch.setattr(run_checks_module, "run_check", run_check)


def test_graph_finishes_after_one_round_when_evidence_is_sufficient(
    tmp_path: Path,
) -> None:
    store = LocalJsonReportStore(tmp_path / "reports.json")
    store.save_report(make_completed_investigation())
    contexts: list[InvestigationContext] = []

    def planner(context: PlanningContext) -> AnalysisPlan:
        assert len(context.historical_matches) == 1
        return make_plan()

    def assessor(context: InvestigationContext) -> EvidenceAssessment:
        contexts.append(context)
        return make_assessment(sufficient=True)

    def writer(context: InvestigationContext) -> RCAReport:
        return make_rca_report(likely_cause="Refunds in payment_type 4")

    graph = build_investigation_graph(
        InvestigationDependencies(
            store=store,
            load_data=lambda _: BATCH,  # ty: ignore[invalid-argument-type]
            planner=planner,
            assessor=assessor,
            report_writer=writer,
        )
    )
    result = graph.invoke({"request": make_request(data_uri="batch.parquet")})

    assert result["iteration_count"] == 1
    assert contexts[0].check_results[0].metrics == {"payment_type=4": 2.0}
    report = result["final_result"].report
    assert report.likely_cause == "Refunds in payment_type 4"
    assert report.previous_similar_incidents == 1
    assert report.analyses_executed == ["breakdown_by(column=fare_amount, group_by=payment_type)"]
    assert report.escalation_required is False


def test_graph_replans_until_cap_then_escalates(tmp_path: Path) -> None:
    rounds: list[PlanningContext] = []

    def planner(context: PlanningContext) -> AnalysisPlan:
        rounds.append(context)
        if len(rounds) == 1:
            return make_plan()
        return make_plan(PlannedCheck(check_name="value_range", column="fare_amount", reason="r"))

    graph = build_investigation_graph(
        InvestigationDependencies(
            store=LocalJsonReportStore(tmp_path / "reports.json"),
            load_data=lambda _: BATCH,  # ty: ignore[invalid-argument-type]
            planner=planner,
            assessor=lambda _: make_assessment(sufficient=False, open_questions=["Why?"]),
            report_writer=lambda _: make_rca_report(),
            max_iterations=2,
        )
    )
    result = graph.invoke({"request": make_request(data_uri="batch.parquet")})

    assert len(rounds) == 2
    assert rounds[1].open_questions == ["Why?"]
    assert len(rounds[1].prior_results) == 1
    assert [check.check_name for check in result["check_results"]] == [
        "breakdown_by",
        "value_range",
    ]
    assert result["final_result"].report.escalation_required is True
