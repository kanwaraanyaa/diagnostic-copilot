"""
SQLAlchemy models for persistent storage (MVP: SQLite).
"""

from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import get_settings


class Base(DeclarativeBase):
    pass


class PatientCaseRecord(Base):
    """Persisted patient case for audit/traceability."""
    __tablename__ = "patient_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=True)
    sex = Column(String(16), nullable=True)
    symptoms = Column(Text, default="")
    history = Column(Text, default="")
    labs_json = Column(Text, default="[]")
    clinical_notes = Column(Text, default="")
    case_description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class AnalysisRecord(Base):
    """Persisted analysis report for a patient case."""
    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(64), nullable=False, index=True)
    report_json = Column(Text, nullable=False)
    llm_provider = Column(String(32), default="")
    llm_model = Column(String(64), default="")
    retrieval_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---- engine & session -------------------------------------------------------

def get_engine():
    settings = get_settings()
    return create_engine(settings.database_url, echo=False)


def init_db():
    """Create all tables if they don't exist."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
