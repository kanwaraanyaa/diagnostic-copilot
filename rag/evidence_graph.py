"""
Evidence Graph Engine — Phase 3.
Constructs a structured, bipartite/heterogeneous clinical knowledge and evidence graph
connecting:
- Patient Observations (symptoms, abnormal labs, CXR observations)
- Clinical Hypotheses (differential considerations)
- Evidence Citations ([E1], [E2]...)
- Agent Judgments (GP, Specialist, Radiology, Critic)
"""

from __future__ import annotations

import os
import sys
from typing import Any, Optional
from pydantic import BaseModel, Field

from backend.schemas.patient import Citation
from logger import get_logger

log = get_logger(__name__)


class GraphNode(BaseModel):
    """Node in the clinical evidence graph."""
    id: str
    label: str
    type: str  # "finding" | "hypothesis" | "evidence" | "agent"
    status: str = "neutral"  # "supported" | "contradicted" | "critical" | "neutral"
    category: str = ""  # e.g., "symptom", "lab", "imaging", "differential"
    score: float = 0.0
    details: str = ""


class GraphEdge(BaseModel):
    """Directed edge in the clinical evidence graph."""
    source: str
    target: str
    relation: str  # "SUPPORTS" | "CONTRADICTS" | "SUGGESTS" | "CITES" | "OBSERVES"
    weight: float = 1.0  # Positive for supporting, negative for contradicting
    explanation: str = ""


class EvidenceGraphResult(BaseModel):
    """Complete serialized evidence graph structure with analytics."""
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    hypothesis_scores: dict[str, float] = Field(default_factory=dict)
    grounding_density: float = 0.0  # % of hypotheses backed by validated evidence
    contradiction_count: int = 0
    total_nodes: int = 0
    total_edges: int = 0
    graph_summary: str = ""


def build_evidence_graph(
    patient_case: dict[str, Any],
    report: Optional[dict[str, Any]] = None,
    citations: Optional[list[dict[str, Any] | Citation]] = None,
    image_findings: Optional[list[dict[str, Any]]] = None,
) -> EvidenceGraphResult:
    """
    Constructs an evidence graph linking patient findings, literature citations,
    agent assessments, and differential diagnostic hypotheses.
    """
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    node_ids: set[str] = set()

    def add_node(n: GraphNode) -> None:
        if n.id not in node_ids:
            node_ids.add(n.id)
            nodes.append(n)

    # 1. Extract Findings from Patient Case
    symptoms = patient_case.get("symptoms", [])
    if isinstance(symptoms, str):
        symptoms = [s.strip() for s in symptoms.split(",") if s.strip()]

    for i, s in enumerate(symptoms[:6]):
        nid = f"finding_sym_{i}"
        add_node(
            GraphNode(
                id=nid,
                label=s.title(),
                type="finding",
                status="neutral",
                category="symptom",
                details=f"Presenting symptom reported in case intake: {s}",
            )
        )

    # Abnormal labs
    labs = patient_case.get("labs", [])
    for i, l in enumerate(labs):
        if isinstance(l, dict) and l.get("is_abnormal"):
            name = l.get("name", "Lab")
            val = l.get("value", "")
            unit = l.get("unit", "")
            nid = f"finding_lab_{i}"
            add_node(
                GraphNode(
                    id=nid,
                    label=f"{name}: {val} {unit}".strip(),
                    type="finding",
                    status="critical",
                    category="lab",
                    details=f"Abnormal laboratory value. Ref: {l.get('reference_range', 'N/A')}",
                )
            )

    # Imaging findings
    if image_findings:
        for i, img_f in enumerate(image_findings[:4]):
            f_name = img_f.get("finding", "Radiologic Observation")
            loc = img_f.get("location", "")
            nid = f"finding_img_{i}"
            add_node(
                GraphNode(
                    id=nid,
                    label=f"CXR: {f_name}" + (f" ({loc})" if loc else ""),
                    type="finding",
                    status="critical" if img_f.get("severity") in ("moderate", "severe") else "neutral",
                    category="imaging",
                    details=img_f.get("details", f"Visual observation: {f_name}"),
                )
            )

    # 2. Extract Citations
    raw_citations = citations or []
    citation_nodes_map: dict[str, str] = {}
    for i, cit in enumerate(raw_citations[:8]):
        c_id = cit.get("source_id") if isinstance(cit, dict) else getattr(cit, "source_id", f"E{i+1}")
        c_title = cit.get("title") if isinstance(cit, dict) else getattr(cit, "title", "Evidence")
        c_score = cit.get("relevance_score") if isinstance(cit, dict) else getattr(cit, "relevance_score", 0.5)
        nid = f"evidence_{c_id}"
        citation_nodes_map[c_id] = nid
        add_node(
            GraphNode(
                id=nid,
                label=f"[{c_id}] {c_title[:24]}",
                type="evidence",
                status="supported",
                category="literature",
                score=round(float(c_score), 2),
                details=cit.get("content", "")[:180] if isinstance(cit, dict) else getattr(cit, "content", "")[:180],
            )
        )

    # 3. Extract Differential Hypotheses from report
    hypothesis_scores: dict[str, float] = {}
    contradiction_count = 0

    differentials = []
    if report:
        differentials = report.get("differential_considerations", [])
        if not differentials and "final_report" in report:
            differentials = report.get("final_report", {}).get("differential_considerations", [])

    if not differentials:
        # Fallback heuristic hypotheses if report not yet synthesized
        symptom_str = " ".join(symptoms).lower()
        if "cough" in symptom_str or "fever" in symptom_str:
            differentials.append({
                "condition": "Community-Acquired Pneumonia",
                "uncertainty": "moderate",
                "supporting_evidence": ["fever", "cough", "leukocytosis"],
                "contradicting_evidence": [],
                "source_ids": list(citation_nodes_map.keys())[:2],
            })
        if "chest pain" in symptom_str or "pressure" in symptom_str or "dyspnea" in symptom_str:
            differentials.append({
                "condition": "Acute Coronary Syndrome",
                "uncertainty": "high",
                "supporting_evidence": ["chest pain", "dyspnea"],
                "contradicting_evidence": ["absence of troponin elevation"],
                "source_ids": list(citation_nodes_map.keys())[2:4],
            })

    for j, diff in enumerate(differentials):
        cond_name = diff.get("condition", f"Condition {j+1}")
        h_id = f"hypo_{j}"
        uncertainty = diff.get("uncertainty", "moderate")

        status = "supported" if uncertainty == "low" else ("critical" if uncertainty == "high" else "neutral")
        add_node(
            GraphNode(
                id=h_id,
                label=cond_name,
                type="hypothesis",
                status=status,
                category="differential",
                details=f"Differential diagnosis. Uncertainty level: {uncertainty}",
            )
        )

        net_score = 0.0

        # Link supporting findings
        supp = diff.get("supporting_evidence", [])
        for sf in supp:
            sf_lower = str(sf).lower()
            # Match finding nodes
            for f_node in [n for n in nodes if n.type == "finding"]:
                if any(w in sf_lower for w in f_node.label.lower().split() if len(w) > 3):
                    edges.append(
                        GraphEdge(
                            source=f_node.id,
                            target=h_id,
                            relation="SUPPORTS",
                            weight=1.0,
                            explanation=f"Finding '{f_node.label}' supports hypothesis '{cond_name}'",
                        )
                    )
                    net_score += 1.0

        # Link contradicting findings
        contra = diff.get("contradicting_evidence", [])
        for cf in contra:
            cf_lower = str(cf).lower()
            for f_node in [n for n in nodes if n.type == "finding"]:
                if any(w in cf_lower for w in f_node.label.lower().split() if len(w) > 3):
                    edges.append(
                        GraphEdge(
                            source=f_node.id,
                            target=h_id,
                            relation="CONTRADICTS",
                            weight=-1.0,
                            explanation=f"Finding '{f_node.label}' contradicts or makes '{cond_name}' less likely",
                        )
                    )
                    net_score -= 1.0
                    contradiction_count += 1

        # Link citation sources
        src_ids = diff.get("source_ids", [])
        for sid in src_ids:
            if sid in citation_nodes_map:
                edges.append(
                    GraphEdge(
                        source=citation_nodes_map[sid],
                        target=h_id,
                        relation="CITES",
                        weight=0.8,
                        explanation=f"Citation [{sid}] provides literature grounding for {cond_name}",
                    )
                )
                net_score += 0.8

        hypothesis_scores[cond_name] = round(net_score, 2)

    # 4. Agent Nodes linkage
    add_node(GraphNode(id="agent_gp", label="GP Agent", type="agent", category="triage", details="Initial triage & risk stratification"))
    add_node(GraphNode(id="agent_specialist", label="Specialist Agent", type="agent", category="cardiopulmonary", details="Differential evaluation"))
    add_node(GraphNode(id="agent_critic", label="Critic Agent", type="agent", category="verification", details="Evidence audit & contradiction checks"))

    # Connect agents to hypotheses
    for h_node in [n for n in nodes if n.type == "hypothesis"]:
        edges.append(GraphEdge(source="agent_specialist", target=h_node.id, relation="SUGGESTS", weight=0.7, explanation="Specialist formulated consideration"))
        edges.append(GraphEdge(source="agent_critic", target=h_node.id, relation="OBSERVES", weight=0.5, explanation="Critic verified claim grounding"))

    # Calculate Grounding Density: fraction of hypotheses with at least 1 CITES or SUPPORTS edge
    hypo_count = len([n for n in nodes if n.type == "hypothesis"])
    supported_hypo_count = 0
    for h_node in [n for n in nodes if n.type == "hypothesis"]:
        has_support = any(
            e.target == h_node.id and e.relation in ("SUPPORTS", "CITES") for e in edges
        )
        if has_support:
            supported_hypo_count += 1

    density = (supported_hypo_count / hypo_count * 100.0) if hypo_count > 0 else 0.0

    summary = (
        f"Evidence graph constructed with {len(nodes)} nodes and {len(edges)} relations. "
        f"Differential grounding density: {density:.1f}%. Detected {contradiction_count} clinical contradictions/exclusions."
    )

    return EvidenceGraphResult(
        nodes=nodes,
        edges=edges,
        hypothesis_scores=hypothesis_scores,
        grounding_density=round(density, 1),
        contradiction_count=contradiction_count,
        total_nodes=len(nodes),
        total_edges=len(edges),
        graph_summary=summary,
    )
