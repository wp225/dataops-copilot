from pathlib import Path

from IPython.display import Image, display

from dataops_copilot.agent.graph import build_investigation_graph
from dataops_copilot.agent.models import AnalysisHypothesis, AnalysisPlan


def fake_planner() -> AnalysisPlan:
    """Provide a placeholder planner solely to compile the graph."""
    return AnalysisPlan(
        analysis_goal="Test graph visualization.",
        hypotheses=[
            AnalysisHypothesis(
                likely_cause="Placeholder",
                rationale="No investigation is executed.",
                likelihood="low",
                checks_to_run=["No checks"],
            )
        ],
    )


graph = build_investigation_graph(
    Path("data/rca_reports.json"),
    fake_planner,
)
Path("docs/diagrams/agents/rca_graph.png").write_bytes(graph.get_graph().draw_mermaid_png())
