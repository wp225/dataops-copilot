"""LangGraph workflow for RCA investigations."""

from pathlib import Path
from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from dataops_copilot.agent.nodes.history import make_search_history_node
from dataops_copilot.agent.nodes.planner import Planner, make_plan_analysis_node
from dataops_copilot.agent.state import InvestigationState


def build_investigation_graph(rca_dump_path: Path | str, planner: Planner) -> CompiledStateGraph:
    """Initial RCA graph with historic case reterival."""
    workflow = StateGraph(InvestigationState)

    workflow.add_node(
        "historic_search",
        make_search_history_node(rca_dump_path),
    )
    workflow.add_node(
        "analysis_planning",
        cast("Any", make_plan_analysis_node(planner)),
    )
    workflow.add_edge(START, "historic_search")
    workflow.add_edge("historic_search", "analysis_planning")
    workflow.add_edge("analysis_planning", END)

    return workflow.compile()
