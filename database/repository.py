"""
Repository layer — abstracts database operations for future PostgreSQL migration.
"""

from __future__ import annotations

import json
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Any

from backend.schemas.patient import DiagnosticReport, PatientCase
from database.models import AnalysisRecord, PatientCaseRecord, get_session, init_db
from logger import get_logger

log = get_logger(__name__)


class CaseRepository:
    """CRUD operations for patient cases and analysis records."""

    def __init__(self) -> None:
        init_db()

    def save_case(self, case: PatientCase) -> str:
        """Persist a patient case. Returns the case_id."""
        session = get_session()
        try:
            existing = session.query(PatientCaseRecord).filter_by(case_id=case.case_id).first()
            if existing:
                existing.age = case.patient.age
                existing.sex = case.patient.sex.value
                existing.symptoms = ",".join(case.symptoms)
                existing.history = ",".join(case.history)
                existing.labs_json = json.dumps([l.model_dump() for l in case.labs])
                existing.clinical_notes = case.clinical_notes
                existing.case_description = case.case_description
            else:
                record = PatientCaseRecord(
                    case_id=case.case_id,
                    age=case.patient.age,
                    sex=case.patient.sex.value,
                    symptoms=",".join(case.symptoms),
                    history=",".join(case.history),
                    labs_json=json.dumps([l.model_dump() for l in case.labs]),
                    clinical_notes=case.clinical_notes,
                    case_description=case.case_description,
                )
                session.add(record)
            session.commit()
            log.info("case_saved", case_id=case.case_id)
            return case.case_id
        except Exception as e:
            session.rollback()
            log.error("case_save_failed", error=str(e))
            raise
        finally:
            session.close()

    def save_analysis(self, report: DiagnosticReport, llm_provider: str = "", llm_model: str = "") -> None:
        """Persist an analysis report."""
        session = get_session()
        try:
            record = AnalysisRecord(
                case_id=report.case_id,
                report_json=report.model_dump_json(),
                llm_provider=llm_provider,
                llm_model=llm_model,
                retrieval_count=len(report.citations),
            )
            session.add(record)
            session.commit()
            log.info("analysis_saved", case_id=report.case_id)
        except Exception as e:
            session.rollback()
            log.error("analysis_save_failed", error=str(e))
            raise
        finally:
            session.close()

    def get_case(self, case_id: str) -> dict[str, Any] | None:
        """Retrieve a saved case by ID."""
        session = get_session()
        try:
            record = session.query(PatientCaseRecord).filter_by(case_id=case_id).first()
            if record is None:
                return None
            return {
                "case_id": record.case_id,
                "age": record.age,
                "sex": record.sex,
                "symptoms": record.symptoms.split(",") if record.symptoms else [],
                "history": record.history.split(",") if record.history else [],
                "labs": json.loads(record.labs_json) if record.labs_json else [],
                "clinical_notes": record.clinical_notes,
                "case_description": record.case_description,
                "created_at": record.created_at.isoformat() if record.created_at else "",
            }
        finally:
            session.close()

    def get_analysis(self, case_id: str) -> dict[str, Any] | None:
        """Retrieve the latest analysis for a case."""
        session = get_session()
        try:
            record = (
                session.query(AnalysisRecord)
                .filter_by(case_id=case_id)
                .order_by(AnalysisRecord.created_at.desc())
                .first()
            )
            if record is None:
                return None
            return json.loads(record.report_json)
        finally:
            session.close()

    def list_cases(self, limit: int = 50) -> list[dict[str, Any]]:
        """Retrieve recent saved cases."""
        session = get_session()
        try:
            records = (
                session.query(PatientCaseRecord)
                .order_by(PatientCaseRecord.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "case_id": r.case_id,
                    "age": r.age,
                    "sex": r.sex,
                    "symptoms": [s.strip() for s in r.symptoms.split(",") if s.strip()] if r.symptoms else [],
                    "history": [h.strip() for h in r.history.split(",") if h.strip()] if r.history else [],
                    "labs": json.loads(r.labs_json) if r.labs_json else [],
                    "clinical_notes": r.clinical_notes,
                    "case_description": r.case_description,
                    "created_at": r.created_at.isoformat() if r.created_at else "",
                }
                for r in records
            ]
        finally:
            session.close()

