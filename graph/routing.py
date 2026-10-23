"""
Conditional routing logic for the LangGraph multi-agent diagnostic workflow — Phase 2.
"""

from __future__ import annotations

from graph.state import DiagnosticState
from logger import get_logger

log = get_logger(__name__)

MAX_DEBATE_ITERATIONS = 3


def should_revise(state: DiagnosticState) -> str:
    """
    Decide whether to execute a debate/retrieval revision cycle or proceed to final synthesis.
    """
    iteration = state.get("iteration_count", 0)
    critic_feedback = state.get("critic_feedback", {})
    revision_required = bool(critic_feedback.get("revision_required", False))

    if revision_required and iteration < MAX_DEBATE_ITERATIONS:
        log.info(
            "routing_revision_cycle",
            iteration=iteration,
            max_iterations=MAX_DEBATE_ITERATIONS,
            missing_evidence=critic_feedback.get("missing_evidence", []),
        )
        return "retrieve_again"

    log.info("routing_to_synthesis", iteration=iteration, revision_required=revision_required)
    return "synthesize"
