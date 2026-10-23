"""
Pydantic schemas for patient data, API requests, and responses.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Enums
# =============================================================================

class Sex(str, Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "Other"
    UNKNOWN = "Unknown"


class UncertaintyLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    UNKNOWN = "unknown"


class DocumentType(str, Enum):
    GUIDELINE = "clinical_guideline"
    PEER_REVIEWED = "peer_reviewed"
    DATABASE = "medical_database"
    EDUCATIONAL = "educational"
    CASE_REPORT = "case_report"
    UNKNOWN = "unknown"


# =============================================================================
# Patient Schemas
# =============================================================================

class LabResult(BaseModel):
    """A single laboratory result."""
    name: str = Field(..., min_length=1, description="Lab test name, e.g. 'WBC'")
    value: float = Field(..., description="Numeric result value")
    unit: str = Field(default="", description="Unit of measure, e.g. 'mg/dL'")
    reference_range: str = Field(default="", description="Normal range, e.g. '4.5-11.0'")
    is_abnormal: Optional[bool] = Field(default=None, description="Whether the value is outside normal range")


class PatientInfo(BaseModel):
    """Core patient demographics."""
    age: Optional[int] = Field(default=None, ge=0, le=150, description="Patient age in years")
    sex: Sex = Field(default=Sex.UNKNOWN)


class PatientCase(BaseModel):
    """Full structured patient case for analysis."""
    case_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    patient: PatientInfo = Field(default_factory=PatientInfo)
    symptoms: list[str] = Field(default_factory=list, description="List of reported symptoms")
    history: list[str] = Field(default_factory=list, description="Relevant medical history")
    labs: list[LabResult] = Field(default_factory=list, description="Laboratory results")
    clinical_notes: str = Field(default="", description="Free-text clinical notes")
    case_description: str = Field(default="", description="Optional case summary or known diagnosis")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("symptoms", mode="before")
    @classmethod
    def clean_symptoms(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return [str(s).strip() for s in v if str(s).strip()]

    @field_validator("history", mode="before")
    @classmethod
    def clean_history(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [h.strip() for h in v.split(",") if h.strip()]
        return [str(h).strip() for h in v if str(h).strip()]


# =============================================================================
# Citation / Evidence Schemas
# =============================================================================

class Citation(BaseModel):
    """A single piece of retrieved evidence."""
    source_id: str = Field(..., description="Unique evidence identifier, e.g. 'E1'")
    title: str = Field(default="")
    source: str = Field(default="", description="Origin file or URL")
    document_type: DocumentType = Field(default=DocumentType.UNKNOWN)
    content: str = Field(default="", description="Relevant text excerpt")
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    chunk_id: str = Field(default="")
    section: str = Field(default="")


# =============================================================================
# Report Schemas
# =============================================================================

class DifferentialCondition(BaseModel):
    """A single differential-diagnosis consideration."""
    condition: str
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    uncertainty: UncertaintyLevel = Field(default=UncertaintyLevel.UNKNOWN)
    source_ids: list[str] = Field(default_factory=list, description="Evidence IDs supporting this condition")


class DiagnosticReport(BaseModel):
    """Phase 1 evidence-grounded diagnostic support report."""
    case_id: str
    patient_summary: str = ""
    important_findings: list[str] = Field(default_factory=list)
    differential_considerations: list[DifferentialCondition] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    disclaimer: str = Field(
        default=(
            "⚠️ FOR RESEARCH AND EDUCATIONAL USE ONLY. "
            "This system does not provide a medical diagnosis and must not replace "
            "evaluation by a qualified healthcare professional."
        )
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    errors: list[str] = Field(default_factory=list)


# =============================================================================
# API Request / Response Schemas
# =============================================================================

class PatientCaseRequest(BaseModel):
    """API request to create/analyze a patient case."""
    patient_id: str = Field(default="", description="Optional patient identifier")
    age: Optional[int] = Field(default=None, ge=0, le=150)
    sex: str = Field(default="Unknown")
    symptoms: str | list[str] = Field(default="")
    history: str | list[str] = Field(default="")
    clinical_notes: str = Field(default="")
    case_description: str = Field(default="")
    labs: list[dict[str, Any]] = Field(default_factory=list, description="Lab results as dicts")
    image_path: Optional[str] = Field(default=None, description="Optional path to uploaded medical image")


class AnalysisResponse(BaseModel):
    """API response wrapping the diagnostic report."""
    success: bool = True
    report: Optional[DiagnosticReport] = None
    error: Optional[str] = None


class AgenticAnalysisResponse(BaseModel):
    """API response for LangGraph multi-agent diagnostic copilot."""
    success: bool = True
    case_id: str = ""
    iteration_count: int = 1
    final_report: dict[str, Any] = Field(default_factory=dict)
    agent_logs: list[dict[str, Any]] = Field(default_factory=list)
    image_findings: list[dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


class VisionAnalysisResponse(BaseModel):
    """API response for medical vision image analysis."""
    success: bool = True
    image_path: str = ""
    image_modality: str = "Chest Radiograph"
    findings: list[dict[str, Any]] = Field(default_factory=list)
    overall_impression: str = ""
    technical_quality: str = "adequate"
    model_used: str = ""
    error: Optional[str] = None


class RetrievalRequest(BaseModel):
    """API request for standalone retrieval."""
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)


class RetrievalResponse(BaseModel):
    """API response for retrieval."""
    success: bool = True
    results: list[Citation] = Field(default_factory=list)
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health-check response."""
    status: str = "ok"
    version: str = "0.3.0"
    phase: int = 3
