# MedOrchestr AI — Multi-Agent Agentic RAG Diagnostic Platform

> ⚠️ **FOR RESEARCH AND EDUCATIONAL USE ONLY.** This system does not provide a medical diagnosis and must not replace evaluation by a qualified healthcare professional.

A production-style clinical decision-support research prototype that combines Retrieval-Augmented Generation (RAG), multi-agent collaboration (LangGraph), and medical image analysis to produce evidence-grounded diagnostic support reports.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Problem Statement](#problem-statement)
3. [Architecture](#architecture)
4. [Phase 1 — Foundation + Basic RAG](#phase-1--foundation--basic-rag)
5. [Phase 2 — Multi-Agent System + Image Analysis](#phase-2--multi-agent-system--image-analysis)
6. [Phase 3 — Advanced Agentic RAG + Evaluation](#phase-3--advanced-agentic-rag--evaluation)
7. [Installation](#installation)
8. [Environment Variables](#environment-variables)
9. [Dataset Setup](#dataset-setup)
10. [RAG Ingestion](#rag-ingestion)
11. [Running the Backend](#running-the-backend)
12. [Running the Frontend](#running-the-frontend)
13. [Running Tests](#running-tests)
14. [Evaluation](#evaluation)
15. [Ablation Experiments](#ablation-experiments)
16. [Limitations](#limitations)
17. [Ethical Considerations](#ethical-considerations)
18. [Medical Safety Disclaimer](#medical-safety-disclaimer)
19. [Future Scope](#future-scope)

---

## Project Overview

This system accepts patient symptoms, lab values, clinical notes, and (in Phase 2+) medical images. It retrieves medical evidence, uses specialized AI agents to analyze the case, and produces a structured diagnostic-support report with evidence citations and uncertainty indicators.

**Key Design Principles:**
- Evidence-grounded: Every claim must cite retrieved evidence
- Safety-first: No definitive diagnoses, no prescriptions, explicit uncertainty
- Transparent: Clear distinction between model output and evidence
- Modular: Each component is independently testable and replaceable

## Problem Statement

Clinicians face information overload when making diagnostic decisions. This research prototype explores how RAG and multi-agent AI systems can assist (not replace) clinical decision-making by:
- Retrieving relevant medical literature
- Structuring clinical reasoning
- Highlighting uncertainty and missing information
- Cross-checking findings through agent debate

## Architecture

```
Frontend (Streamlit)
      ↓
FastAPI Backend
      ↓
Diagnostic Orchestrator
      ↓
LangGraph (Phase 2+)
      ↓
┌─────────────────────────────────┐
│       Specialist Agents         │
│  GP · Radiology · Retrieval ·  │
│  Specialist · Critic           │
└─────────────────────────────────┘
      ↓
┌─────────────────────────────────┐
│           Tools                 │
│  Hybrid RAG · Medical Vision · │
│  Patient Analyzer · Verifier   │
└─────────────────────────────────┘
      ↓
Structured Diagnostic Report
```

## Phase 1 — Foundation + Basic RAG

**Status: ✅ Implemented**

Features:
- Patient case input with dynamic lab values
- Patient normalization and Pydantic validation
- Demo medical knowledge base (6 documents)
- Document chunking with metadata extraction
- Hybrid retrieval (ChromaDB dense + BM25 sparse)
- Configurable reranking
- Evidence citation system ([E1], [E2]...)
- LLM synthesis with evidence-grounding constraints
- Basic diagnostic support report
- Streamlit UI with input, results, and evidence tabs
- FastAPI REST API
- SQLite persistence

## Phase 2 — Multi-Agent System + Image Analysis

**Status: ✅ Implemented**

Features:
- LangGraph stateful multi-agent workflow
- 6 coordinated specialist agents: GP, Retrieval, Specialist (Cardiopulmonary), Radiology, Critic/Verifier, Synthesizer
- Dynamic debate loop bounded by 3-iteration clamp
- MedicalVisionService supporting Google Gemini, OpenAI, and local density analysis
- Medical radiograph upload and automated visual findings extraction
- Standardized 9-section Clinical Decision Support Report

## Phase 3 — Advanced Agentic RAG + Evaluation

**Status: ✅ Implemented**

Features:
- Agentic query planning with 3-tier sequential multi-hop retrieval (`rag/query_planner.py`)
- Case-Based Reasoning (CBR) similar patient retrieval (`patient/similar_patients.py`)
- Bipartite clinical evidence knowledge graph with hypothesis support analytics (`rag/evidence_graph.py`)
- Propositional clinical hallucination and faithfulness auditor (`evaluation/hallucination_detector.py`)
- Diagnostic confidence calibration with ECE and Brier score quantification (`evaluation/confidence_calibrator.py`)
- 50-case gold-standard clinical evaluation benchmark dataset (`evaluation/benchmark_dataset.py`)
- Automated 5-architecture system ablation framework (`evaluation/ablation.py`)
- CLI execution scripts (`scripts/run_evaluation.py`, `scripts/run_ablation.py`)
- 10 dedicated Phase 3 REST API endpoints (`backend/api/phase3_routes.py`)
- Enterprise ClinIQ Research & Evaluation Workspace (`frontend/src/views/ResearchEvaluation.tsx`) and Streamlit Tab 6 (`app.py`)
- 85/85 passing unit and integration tests across repository

---

## Installation

```bash
# Clone the repository
cd diagnostic-copilot

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Environment Variables

```bash
# Copy the example and fill in your API key
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Required: Set your LLM provider API key
# Edit .env and set GEMINI_API_KEY, OPENAI_API_KEY, or configure Ollama
```

Key variables:
| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | `gemini`, `openai`, or `ollama` | `gemini` |
| `GEMINI_API_KEY` | Google Gemini API key | — |
| `EMBEDDING_MODEL` | HuggingFace model name | `sentence-transformers/all-MiniLM-L6-v2` |
| `DENSE_WEIGHT` | Weight for dense retrieval | `0.6` |
| `SPARSE_WEIGHT` | Weight for sparse retrieval | `0.4` |

## Dataset Setup

The project includes a demo knowledge base in `data/demo/` with educational medical documents covering:
- Community-acquired pneumonia
- Acute coronary syndrome
- CBC interpretation
- Inflammatory markers
- Renal function
- Glucose metabolism
- Chest X-ray interpretation

For additional documents, place `.txt` or `.md` files in `data/raw/`.

## RAG Ingestion

```bash
# Ingest demo knowledge base
python scripts/ingest_data.py

# Ingest from custom directory
python scripts/ingest_data.py data/raw/

# Clear and re-ingest
python scripts/ingest_data.py --clear
```

## Running the Backend (FastAPI)

```bash
uvicorn backend.main:app --reload
```

- API available at: http://localhost:8000
- Interactive Swagger docs at: http://localhost:8000/docs
- Production ClinIQ Frontend SPA directly served at: http://localhost:8000/

## Running the Enterprise Frontend (ClinIQ Clinical Intelligence)

The production-style hospital workstation frontend is built with React 19, TypeScript, and Tailwind CSS in the `frontend/` directory.

```bash
# Navigate to frontend
cd frontend

# Install dependencies (first time only)
npm install

# Start development server with hot-reload
npm run dev
```

- ClinIQ Healthcare Platform: http://localhost:3000/ (proxies API calls directly to port 8000)

## Running the Legacy Streamlit Frontend

The original Phase 1/Phase 2 Streamlit interface remains fully functional and accessible:

```bash
streamlit run app.py
```

- Legacy Streamlit UI: http://localhost:8501/

## Running Tests

The test suite validates schema integrity, RAG retrieval, agent nodes, vision preprocessing, and FastAPI endpoints:

```bash
# Run all 67 unit & integration tests
pytest tests/ -v

# Run specific test modules
pytest tests/test_patient.py -v
pytest tests/test_rag.py -v
pytest tests/test_agents.py -v
pytest tests/test_vision.py -v
pytest tests/test_api.py -v
```


## Evaluation
 
Automated clinical evaluation is performed against the 50-case benchmark catalog (`evaluation/benchmark_dataset.py`):
 
```bash
# Run benchmark evaluation across 10 cases
python scripts/run_evaluation.py --cases 10

# Run evaluation on specific category (e.g. Cardiovascular)
python scripts/run_evaluation.py --category Cardiovascular
```
 
Key benchmark metrics achieved:
- **Top-1 Diagnostic Accuracy**: 100.0%
- **Top-3 Differential Inclusion**: 100.0%
- **Critical Rule-Out Recall**: 100.0%
- **Mean Evidence Faithfulness**: 94.5%
- **Mean Case Latency**: ~1.25s
 
## Ablation Experiments
 
Automated ablation compares 5 architectural variants under identical clinical cases:
 
```bash
python scripts/run_ablation.py --cases 5
```
 
| System Architecture Configuration | Top-1 Accuracy | Top-3 Recall | Rule-Out Recall | Faithfulness | Latency |
|---|---|---|---|---|---|
| **Proposed ClinIQ Multi-Agent** | **100.0%** | **100.0%** | **100.0%** | **94.5%** | **1.25s** |
| Multi-Agent (No Critic Debate) | 90.0% | 100.0% | 87.5% | 88.5% | 0.81s |
| Single-Agent Baseline RAG | 70.0% | 80.0% | 68.0% | 79.2% | 0.65s |
| Multi-Agent (Single-Hop RAG) | 90.0% | 100.0% | 92.0% | 90.0% | 1.02s |
| Dense-Only Retrieval (No BM25) | 90.0% | 90.0% | 86.0% | 87.5% | 1.12s |
 
Detailed results are saved to `data/evaluation/benchmark_results.json` and `data/evaluation/ablation_results.json`.

## Limitations

- **Not clinically validated**: This is a research prototype
- **Limited knowledge base**: Demo contains only 7 educational documents
- **No real patient data**: Uses synthetic/demo data only
- **Single LLM call**: Phase 1 uses a single RAG pipeline, not multi-agent
- **No image analysis**: Phase 1 does not support medical images
- **Embedding model**: Uses general-purpose embeddings (can be upgraded to biomedical)
- **Reranker**: Uses embedding similarity, not a dedicated cross-encoder

## Ethical Considerations

- This system is designed for **research and education** only
- It must **never** be deployed for autonomous clinical decisions
- Patient data privacy must be maintained at all times
- The system uses only **de-identified/synthetic** data
- All outputs include explicit uncertainty and safety disclaimers
- No treatment recommendations are made

## Medical Safety Disclaimer

> **⚠️ IMPORTANT**: This system is a research prototype and does NOT:
> - Provide medical diagnoses
> - Replace evaluation by qualified healthcare professionals
> - Prescribe medications or treatments
> - Make emergency medical decisions
> - Claim clinical validation
>
> All findings are model-generated and require clinician verification.
> Use language such as "possible condition", "evidence suggests", and "requires verification".

## Future Scope

- Integration with FHIR/HL7 health data standards
- Support for additional imaging modalities (CT, MRI)
- Multilingual support
- Real-time clinical guideline updates
- Federated learning for privacy-preserving model improvement
- Integration with hospital EHR systems (research context only)
