"""
FastAPI API routes for the Diagnostic Copilot.
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.schemas.patient import (
    AgenticAnalysisResponse,
    AnalysisResponse,
    HealthResponse,
    PatientCase,
    PatientCaseRequest,
    RetrievalRequest,
    RetrievalResponse,
    VisionAnalysisResponse,
)
from backend.services.llm_service import get_llm_provider
from backend.services.rag_service import run_rag_pipeline
from graph.workflow import run_diagnostic_workflow
from vision.medical_vision import MedicalVisionService
from database.repository import CaseRepository
from logger import get_logger
from patient.normalizer import normalize_patient_case
from patient.validators import validate_patient_input
from rag.bm25 import BM25Index
from rag.citations import build_citations
from rag.hybrid_search import hybrid_search
from rag.ingestion import ensure_indexes_loaded
from rag.reranker import rerank
from rag.vector_store import VectorStore

log = get_logger(__name__)

router = APIRouter(prefix="/api")

# Lazy-initialized singletons
_vs: VectorStore | None = None
_bm: BM25Index | None = None
_repo: CaseRepository | None = None


def _get_indexes() -> tuple[VectorStore, BM25Index]:
    global _vs, _bm
    if _vs is None or _bm is None:
        _vs, _bm = ensure_indexes_loaded()
    return _vs, _bm


def _get_repo() -> CaseRepository:
    global _repo
    if _repo is None:
        _repo = CaseRepository()
    return _repo


# ---- Health ----------------------------------------------------------------

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse()


# ---- Cases -----------------------------------------------------------------

@router.post("/cases", response_model=dict)
async def create_case(request: PatientCaseRequest):
    """Create and persist a patient case."""
    try:
        raw = {
            "patient_id": request.patient_id,
            "age": request.age,
            "sex": request.sex,
            "symptoms": request.symptoms,
            "history": request.history,
            "clinical_notes": request.clinical_notes,
            "case_description": request.case_description,
            "labs": request.labs,
        }
        warnings = validate_patient_input(raw)
        case = normalize_patient_case(raw)
        _get_repo().save_case(case)

        return {
            "success": True,
            "case_id": case.case_id,
            "warnings": warnings,
        }
    except Exception as e:
        log.error("create_case_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cases", response_model=list[dict])
async def list_cases(limit: int = 50):
    """Retrieve recent saved patient cases."""
    try:
        return _get_repo().list_cases(limit=limit)
    except Exception as e:
        log.error("list_cases_failed", error=str(e))
        return []


@router.get("/cases/{case_id}")
async def get_case(case_id: str):
    """Retrieve a saved case."""
    result = _get_repo().get_case(case_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return result



# ---- Analysis ---------------------------------------------------------------

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_case(request: PatientCaseRequest):
    """Run the full RAG analysis pipeline on a patient case."""
    try:
        raw = {
            "patient_id": request.patient_id,
            "age": request.age,
            "sex": request.sex,
            "symptoms": request.symptoms,
            "history": request.history,
            "clinical_notes": request.clinical_notes,
            "case_description": request.case_description,
            "labs": request.labs,
        }
        case = normalize_patient_case(raw)

        # Save case
        try:
            _get_repo().save_case(case)
        except Exception:
            pass  # Non-critical

        # Run RAG pipeline
        vs, bm = _get_indexes()
        report = run_rag_pipeline(case, vector_store=vs, bm25_index=bm)

        # Save analysis
        try:
            _get_repo().save_analysis(report)
        except Exception:
            pass  # Non-critical

        return AnalysisResponse(success=True, report=report)

    except Exception as e:
        log.error("analyze_failed", error=str(e))
        return AnalysisResponse(success=False, error=str(e))


# ---- Retrieval --------------------------------------------------------------

@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve_evidence(request: RetrievalRequest):
    """Standalone hybrid retrieval endpoint."""
    try:
        vs, bm = _get_indexes()
        results = hybrid_search(request.query, vs, bm, top_k=request.top_k * 2)
        reranked = rerank(request.query, results, top_k=request.top_k)
        citations = build_citations(reranked)
        return RetrievalResponse(success=True, results=citations)
    except Exception as e:
        log.error("retrieve_failed", error=str(e))
        return RetrievalResponse(success=False, error=str(e))


# ---- Phase 2: Agentic Multi-Agent Orchestration -----------------------------

@router.post("/analyze/agentic", response_model=AgenticAnalysisResponse)
async def analyze_case_agentic(request: PatientCaseRequest):
    """
    Execute the stateful LangGraph multi-agent diagnostic workflow.
    Involves: GP Agent -> Retrieval Agent -> Specialist -> Radiologist -> Critic -> Synthesizer.
    """
    try:
        raw = {
            "patient_id": request.patient_id,
            "age": request.age,
            "sex": request.sex,
            "symptoms": request.symptoms,
            "history": request.history,
            "clinical_notes": request.clinical_notes,
            "case_description": request.case_description,
            "labs": request.labs,
        }
        case = normalize_patient_case(raw)

        # Persist case
        try:
            _get_repo().save_case(case)
        except Exception:
            pass

        # Execute LangGraph workflow
        final_state = run_diagnostic_workflow(
            patient_case=case.model_dump(),
            image_path=request.image_path,
        )

        return AgenticAnalysisResponse(
            success=True,
            case_id=case.case_id,
            iteration_count=final_state.get("iteration_count", 1),
            final_report=final_state.get("final_report", {}),
            agent_logs=final_state.get("agent_logs", []),
            image_findings=final_state.get("image_findings", []),
        )

    except Exception as e:
        log.error("agentic_analysis_failed", error=str(e))
        return AgenticAnalysisResponse(success=False, error=str(e))


# ---- Phase 2: Medical Vision Upload & Analysis ------------------------------

@router.post("/upload/image", response_model=dict)
async def upload_image(file: UploadFile = File(...)):
    """Upload and save an image temporarily for analysis."""
    try:
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest_path = upload_dir / f"upload_{file.filename}"

        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "success": True,
            "image_path": str(dest_path),
            "filename": file.filename,
        }
    except Exception as e:
        log.error("image_upload_failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze/image", response_model=VisionAnalysisResponse)
async def analyze_image_endpoint(file: UploadFile = File(...)):
    """Directly analyze an uploaded radiographic image via MedicalVisionService."""
    try:
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest_path = upload_dir / f"vision_{file.filename}"

        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        vision_service = MedicalVisionService()
        result = vision_service.analyze(dest_path)

        return VisionAnalysisResponse(
            success=True,
            image_path=str(dest_path),
            image_modality=result.image_modality,
            findings=[f.to_dict() for f in result.findings],
            overall_impression=result.overall_impression,
            technical_quality=result.technical_quality,
            model_used=result.model_used,
        )
    except Exception as e:
        log.error("image_analysis_endpoint_failed", error=str(e))
        return VisionAnalysisResponse(success=False, error=str(e))
