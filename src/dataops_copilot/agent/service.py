"""End-to-end orchestration: profile a batch, detect incidents, investigate, persist."""

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from dataops_copilot.agent.graph import InvestigationDependencies, build_investigation_graph
from dataops_copilot.agent.models import IncidentInvestigationRequest, IncidentRCAReport
from dataops_copilot.agent.services.assessor import make_claude_assessor
from dataops_copilot.agent.services.data_loader import DataLoader, make_parquet_loader
from dataops_copilot.agent.services.llm import make_chat_model
from dataops_copilot.agent.services.planner import make_claude_planner
from dataops_copilot.agent.services.report_store import (
    AdlsReportStore,
    LocalJsonReportStore,
    ReportStore,
)
from dataops_copilot.agent.services.report_writer import make_claude_report_writer
from dataops_copilot.quality.detector import detect_incidents
from dataops_copilot.quality.models import DataQualityIncident, QualityReport
from dataops_copilot.quality.policy import QualityPolicy
from dataops_copilot.quality.profiler import calculate_metrics
from dataops_copilot.utils.pyspark_session import spark_session

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph

    from dataops_copilot.config import Settings


class ScanRequest(BaseModel):
    """Ask for one batch to be profiled and, optionally, investigated."""

    dataset_name: str
    batch_id: str
    data_uri: str
    investigate: bool = True


class ScanResult(BaseModel):
    """Quality profile of a batch, its incidents and their RCA reports."""

    dataset_name: str
    batch_id: str
    quality_report: QualityReport
    incidents: list[DataQualityIncident]
    reports: list[IncidentRCAReport] = Field(default_factory=list)


class InvestigationService:
    """Run investigations through the graph and keep their reports."""

    def __init__(
        self,
        graph: "CompiledStateGraph",
        store: ReportStore,
        load_data: DataLoader,
        policy: QualityPolicy | None = None,
    ) -> None:
        self.graph = graph
        self.store = store
        self.load_data = load_data
        self.policy = policy or QualityPolicy()

    def investigate(self, request: IncidentInvestigationRequest) -> IncidentRCAReport:
        """Investigate one incident and persist the resulting report."""
        result: dict[str, Any] = self.graph.invoke({"request": request})
        final = result.get("final_result")
        if final is None:
            message = "Investigation graph finished without a report."
            raise RuntimeError(message)
        report = IncidentRCAReport.model_validate(final)
        self.store.save_report(report)
        return report

    def scan(self, scan: ScanRequest) -> ScanResult:
        """Profile a batch, detect policy violations and investigate each one."""
        quality_report = calculate_metrics(self.load_data(scan.data_uri))
        incidents = detect_incidents(quality_report, self.policy)

        reports = []
        if scan.investigate:
            reports = [
                self.investigate(
                    IncidentInvestigationRequest(
                        incident=incident,
                        quality_report=quality_report,
                        dataset_name=scan.dataset_name,
                        batch_id=scan.batch_id,
                        data_uri=scan.data_uri,
                    )
                )
                for incident in incidents
            ]

        return ScanResult(
            dataset_name=scan.dataset_name,
            batch_id=scan.batch_id,
            quality_report=quality_report,
            incidents=incidents,
            reports=reports,
        )


def build_report_store(settings: "Settings") -> ReportStore:
    """Create the configured report store."""
    if settings.report_store == "adls":
        if not settings.adls_account_url:
            message = "DATAOPS_ADLS_ACCOUNT_URL is required when report_store is 'adls'."
            raise ValueError(message)
        return AdlsReportStore.from_account(settings.adls_account_url, settings.adls_container)
    return LocalJsonReportStore(settings.local_report_path)


def build_service(settings: "Settings") -> InvestigationService:
    """Wire Spark, Claude and storage into a production InvestigationService."""
    llm = make_chat_model(settings.anthropic_model, settings.anthropic_effort)
    store = build_report_store(settings)
    load_data = make_parquet_loader(spark_session(settings.spark_app_name), settings.data_cache_dir)
    graph = build_investigation_graph(
        InvestigationDependencies(
            store=store,
            load_data=load_data,
            planner=make_claude_planner(llm),
            assessor=make_claude_assessor(llm),
            report_writer=make_claude_report_writer(llm),
            max_iterations=settings.max_iterations,
        )
    )
    return InvestigationService(
        graph=graph,
        store=store,
        load_data=load_data,
        policy=QualityPolicy(threshold_rate=settings.quality_threshold_rate),
    )
