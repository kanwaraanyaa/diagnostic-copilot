"""
LangGraph stateful workflow construction and execution — Phase 2.
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Any, Optional
from langgraph.graph import END, START, StateGraph

from agents.critic_agent import critic_agent_node
from agents.gp_agent import gp_agent_node
from agents.radiology_agent import radiology_agent_node
from agents.retrieval_agent import retrieval_agent_node
from agents.specialist_agent import specialist_agent_node
from agents.synthesizer import synthesizer_node
from graph.routing import should_revise
from graph.state import DiagnosticState
from logger import get_logger

log = get_logger(__name__)


def build_diagnostic_graph() -> Any:
    """
    Construct the stateful LangGraph multi-agent diagnostic workflow.

    Workflow topology:
        START
          ↓
       gp_agent
          ↓
       retrieval_agent
          ↓
       specialist_agent
          ↓
       radiology_agent
          ↓
       critic_agent
          ↓ (conditional)
       [should_revise?] ─── "retrieve_again" ───→ retrieval_agent
          │
          └─── "synthesize" ───→ synthesizer ───→ END
    """
    workflow = StateGraph(DiagnosticState)

    # 1. Register agent nodes
    workflow.add_node("gp_agent", gp_agent_node)
    workflow.add_node("retrieval_agent", retrieval_agent_node)
    workflow.add_node("specialist_agent", specialist_agent_node)
    workflow.add_node("radiology_agent", radiology_agent_node)
    workflow.add_node("critic_agent", critic_agent_node)
    workflow.add_node("synthesizer", synthesizer_node)

    # 2. Main linear edges: GP -> Retrieval -> Radiology -> Specialist -> Critic
    workflow.add_edge(START, "gp_agent")
    workflow.add_edge("gp_agent", "retrieval_agent")
    workflow.add_edge("retrieval_agent", "radiology_agent")
    workflow.add_edge("radiology_agent", "specialist_agent")
    workflow.add_edge("specialist_agent", "critic_agent")

    # 3. Conditional debate edge
    workflow.add_conditional_edges(
        "critic_agent",
        should_revise,
        {
            "retrieve_again": "retrieval_agent",
            "synthesize": "synthesizer",
        },
    )

    # 4. Final edge
    workflow.add_edge("synthesizer", END)

    app = workflow.compile()
    log.info("diagnostic_graph_compiled_successfully")
    return app


# Cached graph singleton
_compiled_graph: Any = None


def get_diagnostic_graph() -> Any:
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_diagnostic_graph()
    return _compiled_graph


def run_diagnostic_workflow(
    patient_case: dict[str, Any],
    image_path: Optional[str] = None,
) -> DiagnosticState:
    """
    Execute the multi-agent diagnostic graph on a normalized patient case.
    """
    app = get_diagnostic_graph()

    initial_state: DiagnosticState = {
        "patient_case": patient_case,
        "image_path": image_path,
        "retrieved_evidence": [],
        "image_findings": [],
        "agent_logs": [],
        "agent_reports": [],
        "errors": [],
        "iteration_count": 0,
        "iteration": 0,
    }

    log.info("running_diagnostic_workflow", case_id=patient_case.get("case_id"))
    final_state = app.invoke(initial_state)
    log.info(
        "diagnostic_workflow_completed",
        case_id=patient_case.get("case_id"),
        iterations=final_state.get("iteration_count"),
        logs_count=len(final_state.get("agent_logs", [])),
    )
    return final_state
