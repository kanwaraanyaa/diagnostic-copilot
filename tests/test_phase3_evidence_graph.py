"""
Tests for Clinical Evidence Graph Engine — Phase 3.
"""

from __future__ import annotations

import pytest
from rag.evidence_graph import (
    build_evidence_graph,
    EvidenceGraphResult,
)


@pytest.fixture
def mock_graph_input() -> dict:
    return {
        "patient_case": {
            "case_id": "TEST-GRAPH-001",
            "symptoms": ["cough", "fever", "dyspnea"],
            "labs": [{"name": "WBC", "value": 17.0, "unit": "10^3/uL", "is_abnormal": True}],
        },
        "report": {
            "differential_considerations": [
                {
                    "condition": "Community-Acquired Pneumonia",
                    "uncertainty": "low",
                    "supporting_evidence": ["fever", "cough", "WBC"],
                    "contradicting_evidence": [],
                    "source_ids": ["E1"],
                },
                {
                    "condition": "Acute Heart Failure",
                    "uncertainty": "high",
                    "supporting_evidence": ["dyspnea"],
                    "contradicting_evidence": ["fever"],
                    "source_ids": ["E2"],
                },
            ]
        },
        "citations": [
            {"source_id": "E1", "title": "Pneumonia Guidelines", "relevance_score": 0.85, "content": "CAP diagnostic criteria"},
            {"source_id": "E2", "title": "Heart Failure Management", "relevance_score": 0.70, "content": "ADHF clinical guidelines"},
        ],
        "image_findings": [
            {"finding": "Right lower lobe consolidation", "location": "right base", "severity": "moderate"}
        ],
    }


def test_build_evidence_graph(mock_graph_input: dict):
    graph = build_evidence_graph(
        patient_case=mock_graph_input["patient_case"],
        report=mock_graph_input["report"],
        citations=mock_graph_input["citations"],
        image_findings=mock_graph_input["image_findings"],
    )

    assert isinstance(graph, EvidenceGraphResult)
    assert graph.total_nodes > 5
    assert graph.total_edges > 3

    node_types = {n.type for n in graph.nodes}
    assert "finding" in node_types
    assert "hypothesis" in node_types
    assert "evidence" in node_types
    assert "agent" in node_types

    relations = {e.relation for e in graph.edges}
    assert "SUPPORTS" in relations or "CITES" in relations
    assert graph.grounding_density > 0.0
    assert "Community-Acquired Pneumonia" in graph.hypothesis_scores
