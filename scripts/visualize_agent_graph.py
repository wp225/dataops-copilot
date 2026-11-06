"""Render the RCA investigation graph to docs/diagrams/agents/rca_graph.png."""

from pathlib import Path

from dataops_copilot.agent.graph import InvestigationDependencies, build_investigation_graph
from dataops_copilot.agent.services.report_store import LocalJsonReportStore


def _unused(*_: object) -> object:
    message = "Placeholder dependency; the graph is only compiled, never run."
    raise NotImplementedError(message)


graph = build_investigation_graph(
    InvestigationDependencies(
        store=LocalJsonReportStore("data/rca_reports.json"),
        load_data=_unused,  # ty: ignore[invalid-argument-type]
        planner=_unused,  # ty: ignore[invalid-argument-type]
        assessor=_unused,  # ty: ignore[invalid-argument-type]
        report_writer=_unused,  # ty: ignore[invalid-argument-type]
    )
)
Path("docs/diagrams/agents/rca_graph.png").write_bytes(graph.get_graph().draw_mermaid_png())
