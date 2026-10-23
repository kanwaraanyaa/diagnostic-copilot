"""
Typed State definition for the Multi-Agent Diagnostic Copilot — Phase 2.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict


class DiagnosticState(TypedDict, total=False):
    """
    Shared state exchanged across specialist agents in the LangGraph workflow.
    """
    # Core input
    patient_case: dict[str, Any]
    image_path: Optional[str]

    # Agent assessments & findings
    gp_assessment: dict[str, Any]
    retrieval_queries: list[str]
    retrieved_evidence: list[dict[str, Any]]
    image_findings: list[dict[str, Any]]
    radiology_assessment: dict[str, Any]
    specialist_assessments: dict[str, Any]  # e.g. {"cardiology": {...}, "pulmonology": {...}}
    hypotheses: list[dict[str, Any]]

    # Critic & iterative debate
    critic_feedback: dict[str, Any]
    iteration_count: int
    iteration: int  # Alias for iteration_count

    # Final outputs
    final_report: dict[str, Any]
    confidence: dict[str, Any]
    errors: list[str]
    agent_logs: list[dict[str, Any]]
    agent_reports: list[dict[str, Any]]  # Normalized list of agent reports/actions

    # Phase 3 Advanced Capabilities
    query_plan: dict[str, Any]
    similar_patients: list[dict[str, Any]]
    evidence_graph: dict[str, Any]
    hallucination_audit: dict[str, Any]
    calibration: dict[str, Any]
