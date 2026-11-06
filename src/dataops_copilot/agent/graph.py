"""LangGraph workflow for RCA investigations."""

from dataclasses import dataclass
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from dataops_copilot.agent.nodes.assess import make_assess_evidence_node, make_assessment_router
from dataops_copilot.agent.nodes.history import make_search_history_node
from dataops_copilot.agent.nodes.planner import make_plan_analysis_node
from dataops_copilot.agent.nodes.report import make_write_report_node
from dataops_copilot.agent.nodes.run_checks import make_run_checks_node
from dataops_copilot.agent.services.assessor import Assessor
from dataops_copilot.agent.services.data_loader import DataLoader
from dataops_copilot.agent.services.planner import Planner
from dataops_copilot.agent.services.report_store import ReportStore
from dataops_copilot.agent.services.report_writer import ReportWriter
from dataops_copilot.agent.state import InvestigationState

DEFAULT_MAX_ITERATIONS = 3


@dataclass(frozen=True)
class InvestigationDependencies:
    """The pluggable pieces of an investigation; fakes in tests, Claude/Spark in prod."""

    store: ReportStore
    load_data: DataLoader
    planner: Planner
    assessor: Assessor
    report_writer: ReportWriter
    max_iterations: int = DEFAULT_MAX_ITERATIONS


def build_investigation_graph(deps: InvestigationDependencies) -> CompiledStateGraph:
    """Build the RCA loop.

    historic_search -> analysis_planning -> run_checks -> assess_evidence
        -> (analysis_planning again | write_report) -> END
    """
    workflow = StateGraph(InvestigationState)

    nodes: dict[str, Any] = {
        "historic_search": make_search_history_node(deps.store),
        "analysis_planning": make_plan_analysis_node(deps.planner),
        "run_checks": make_run_checks_node(deps.load_data),
        "assess_evidence": make_assess_evidence_node(deps.assessor),
        "write_report": make_write_report_node(deps.report_writer),
    }
    for name, node in nodes.items():
        workflow.add_node(name, node)

    workflow.add_edge(START, "historic_search")
    workflow.add_edge("historic_search", "analysis_planning")
    workflow.add_edge("analysis_planning", "run_checks")
    workflow.add_edge("run_checks", "assess_evidence")
    workflow.add_conditional_edges(
        "assess_evidence",
        make_assessment_router(deps.max_iterations),
        ["analysis_planning", "write_report"],
    )
    workflow.add_edge("write_report", END)

    return workflow.compile()
