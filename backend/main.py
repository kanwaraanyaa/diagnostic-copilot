"""
FastAPI application entry point.
"""

from __future__ import annotations

import os
import sys

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from logger import setup_logging

setup_logging()

app = FastAPI(
    title="MedOrchestr AI API",
    description=(
        "MedOrchestr AI — Multi-Agent Agentic RAG Diagnostic Intelligence. "
        "A clinical decision-support research prototype. "
        "For research and educational use only. Not medical advice."
    ),
    version="0.3.0",
)

# CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pathlib import Path
from fastapi.staticfiles import StaticFiles

from backend.api.phase3_routes import router as phase3_router

app.include_router(router)
app.include_router(phase3_router)

# Mount static directories for image previews
uploads_dir = Path("data/uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

demo_dir = Path("data/demo")
if demo_dir.exists():
    app.mount("/demo-data", StaticFiles(directory=str(demo_dir)), name="demo-data")

# Mount built frontend SPA if available
frontend_dist = Path("frontend/dist")
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")



@app.on_event("startup")
async def startup_event():
    """Initialize resources on application startup."""
    from config import get_settings
    from logger import get_logger

    log = get_logger("startup")
    settings = get_settings()

    # Ensure data directories exist
    for d in [settings.data_dir, settings.raw_data_dir, settings.processed_data_dir, settings.demo_data_dir]:
        d.mkdir(parents=True, exist_ok=True)

    log.info(
        "application_started",
        llm_provider=settings.llm_provider,
        embedding_model=settings.embedding_model,
    )
