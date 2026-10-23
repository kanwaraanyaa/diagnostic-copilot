"""
FastAPI Routes for Phase 3 — Advanced Agentic RAG, Similar Patients,
Evidence Graph, Hallucination Auditing, Confidence Calibration, and Benchmarks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.schemas.patient import PatientCaseRequest
from evaluation.ablation import AblationStudyResult, run_ablation_study
from evaluation.benchmark_dataset import BENCHMARK_CASES_CATALOG, load_benchmark_cases
from evaluation.benchmark_runner import BenchmarkRunResult, run_benchmark_suite
from evaluation.confidence_calibrator import CalibrationResult, calibrate_differential_confidence
from evaluation.hallucination_detector import HallucinationAuditResult, audit_report_hallucinations
from patient.similar_patients import SimilarPatientResponse, find_similar_patients
from rag.evidence_graph import EvidenceGraphResult, build_evidence_graph
from rag.query_planner import QueryPlanResult, execute_multi_hop_retrieval
from logger import get_logger

log = get_logger(__name__)

router = APIRouter(prefix="/api/phase3", tags=["Phase 3 Research & Evaluation"])


class HallucinationAuditRequest(BaseModel):
    patient_case: dict[str, Any]
    report: dict[str, Any]
    citations: list[dict[str, Any]] = []
    image_findings: list[dict[str, Any]] = []


class CalibrationRequest(BaseModel):
    differentials: list[dict[str, Any]]
    critic_feedback: dict[str, Any] = {}
    citations: list[dict[str, Any]] = []
    missing_info: list[str] = []


# -----------------------------------------------------------------------------
# 1. Multi-Hop Query Planning
# -----------------------------------------------------------------------------
@router.post("/query-plan", response_model=QueryPlanResult)
async def plan_query_endpoint(request: PatientCaseRequest, max_hops: int = Query(default=3, ge=1, le=5)):
    """Decomposes a patient case into multi-hop clinical investigative queries and executes retrieval."""
    try:
        pdict = request.model_dump()
        result = execute_multi_hop_retrieval(patient_case=pdict, max_hops=max_hops)
        return result
    except Exception as e:
        log.error("query_plan_endpoint_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# 2. Similar Patient Case-Based Reasoning Retrieval
# -----------------------------------------------------------------------------
@router.post("/similar-patients", response_model=SimilarPatientResponse)
async def similar_patients_endpoint(request: PatientCaseRequest, top_k: int = Query(default=3, ge=1, le=10)):
    """Retrieves top clinically similar patient encounters from the reference cohort."""
    try:
        pdict = request.model_dump()
        result = find_similar_patients(patient_case=pdict, top_k=top_k)
        return result
    except Exception as e:
        log.error("similar_patients_endpoint_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# 3. Clinical Evidence Graph
# -----------------------------------------------------------------------------
@router.post("/evidence-graph", response_model=EvidenceGraphResult)
async def evidence_graph_endpoint(request: PatientCaseRequest):
    """Constructs a bipartite evidence knowledge graph connecting findings, hypotheses, and citations."""
    try:
        pdict = request.model_dump()
        result = build_evidence_graph(patient_case=pdict)
        return result
    except Exception as e:
        log.error("evidence_graph_endpoint_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# 4. Hallucination Detection & Faithfulness Audit
# -----------------------------------------------------------------------------
@router.post("/hallucination-audit", response_model=HallucinationAuditResult)
async def hallucination_audit_endpoint(payload: HallucinationAuditRequest):
    """Audits report claims for hallucinations, patient-chart grounding, and citation attribution."""
    try:
        result = audit_report_hallucinations(
            patient_case=payload.patient_case,
            report=payload.report,
            citations=payload.citations,
            image_findings=payload.image_findings,
        )
        return result
    except Exception as e:
        log.error("hallucination_audit_endpoint_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# 5. Diagnostic Confidence Calibration
# -----------------------------------------------------------------------------
@router.post("/calibration", response_model=CalibrationResult)
async def calibration_endpoint(payload: CalibrationRequest):
    """Computes Expected Calibration Error (ECE) and multi-factor uncertainty penalties."""
    try:
        result = calibrate_differential_confidence(
            differentials=payload.differentials,
            critic_feedback=payload.critic_feedback,
            citations=payload.citations,
            missing_info=payload.missing_info,
        )
        return result
    except Exception as e:
        log.error("calibration_endpoint_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------------------------------------------------------
# 6. Benchmark Suite Catalog & Execution
# -----------------------------------------------------------------------------
@router.get("/benchmark/cases")
async def get_benchmark_cases():
    """Lists summary catalog of the 50 gold-standard clinical evaluation benchmark cases."""
    return {
        "total_cases": len(BENCHMARK_CASES_CATALOG),
        "cases": [
            {
                "case_id": c["case_id"],
                "category": c["category"],
                "complexity": c["complexity"],
                "age": c["patient"]["age"],
                "sex": c["patient"]["sex"],
                "symptoms_preview": ", ".join(c["symptoms"][:3]),
                "gold_standard_primary": c["gold_standard_primary"],
            }
            for c in BENCHMARK_CASES_CATALOG
        ],
    }


@router.post("/benchmark/run", response_model=BenchmarkRunResult)
async def run_benchmark_endpoint(
    max_cases: int = Query(default=10, ge=1, le=50),
    category: Optional[str] = Query(default=None),
):
    """Executes the automated benchmark evaluation suite on clinical cases."""
    try:
        result = run_benchmark_suite(max_cases=max_cases, category_filter=category)
        return result
    except Exception as e:
        log.error("benchmark_run_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmark/latest")
async def get_latest_benchmark_results():
    """Retrieves the latest persisted benchmark evaluation run results."""
    eval_file = Path("data/evaluation/benchmark_results.json")
    if not eval_file.exists():
        # Run a quick default 5-case benchmark if no run exists yet
        result = run_benchmark_suite(max_cases=5)
        return result
    try:
        with open(eval_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read benchmark results: {e}")


# -----------------------------------------------------------------------------
# 7. Ablation Experiments
# -----------------------------------------------------------------------------
@router.post("/ablation/run", response_model=AblationStudyResult)
async def run_ablation_endpoint(max_cases: int = Query(default=5, ge=1, le=20)):
    """Executes comparative ablation experiments across 5 architectural configurations."""
    try:
        result = run_ablation_study(max_cases=max_cases)
        return result
    except Exception as e:
        log.error("ablation_run_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ablation/latest")
async def get_latest_ablation_results():
    """Retrieves the latest persisted ablation experiment results."""
    eval_file = Path("data/evaluation/ablation_results.json")
    if not eval_file.exists():
        result = run_ablation_study(max_cases=5)
        return result
    try:
        with open(eval_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read ablation results: {e}")
