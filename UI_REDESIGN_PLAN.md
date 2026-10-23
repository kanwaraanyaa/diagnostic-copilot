# UI_REDESIGN_PLAN.md: ClinIQ Clinical Intelligence Workspace Redesign Plan

## 1. Executive Summary & Repository Inspection

### 1.1 Existing Architecture & Technology Stack
- **Backend**: FastAPI (`backend/main.py`, `backend/api/routes.py`), SQLite with SQLAlchemy (`database/models.py`, `database/repository.py`), Pydantic V2 schemas (`backend/schemas/patient.py`).
- **AI / Agentic Engine**: LangGraph stateful workflow (`graph/workflow.py`, `graph/state.py`, `graph/routing.py`) with 6 coordinated agent nodes:
  - `gp_agent` (General Physician triage, clinical indicators, hypotheses, queries)
  - `retrieval_agent` (Targeted RAG execution, query reformulation)
  - `radiology_agent` (Vision findings parsing, calibrated uncertainty, caching)
  - `specialist_agent` (Cardiopulmonary differential, supporting/contradicting findings)
  - `critic_agent` (Citation verification, contradiction detection, bounded revision loop <= 3 iterations)
  - `synthesizer` (Compiles standardized 9-section Clinical Decision Support report)
- **RAG Subsystem**: Dense vector retrieval (ChromaDB `medical_knowledge` collection, `sentence-transformers/all-MiniLM-L6-v2`) + Sparse retrieval (BM25Index) + Lexical cross-matching reranker (`rag/reranker.py`) + Citation linker (`rag/citations.py`).
- **Medical Vision Subsystem**: `MedicalVisionService` (`vision/medical_vision.py`) supporting Gemini Vision, OpenAI Vision, Local Demo adapter (`LocalDemoVisionAdapter`), and preprocessor with normalization/resizing (`vision/preprocessing.py`).
- **Existing Frontend**: Streamlit (`app.py`, 765 lines) with basic dark theme, oversized emojis, single-page tabbed layout, developer-centric phase labels ("Phase 1", "Phase 2").
- **Test Coverage**: 67 passing unit and integration tests (`tests/test_patient.py`, `tests/test_rag.py`, `tests/test_agents.py`, `tests/test_vision.py`, `tests/test_phase2_integration.py`, `tests/test_api.py`).

### 1.2 Backend API Inventory
| Endpoint | Method | Input | Output | Status |
|---|---|---|---|---|
| `/api/health` | GET | None | `HealthResponse` (status, version, phase) | Fully Working |
| `/api/cases` | POST | `PatientCaseRequest` | `{ success: bool, case_id: str, warnings: list }` | Fully Working |
| `/api/cases/{case_id}` | GET | `case_id` | Patient case JSON | Fully Working |
| `/api/cases` *(Extension)* | GET | `limit: int = 20` | `list[PatientCaseRecord]` | To add for real dashboard listing |
| `/api/analyze` | POST | `PatientCaseRequest` | `AnalysisResponse` (Phase 1 Baseline RAG) | Fully Working |
| `/api/analyze/agentic` | POST | `PatientCaseRequest` | `AgenticAnalysisResponse` (LangGraph Multi-Agent) | Fully Working |
| `/api/retrieve` | POST | `RetrievalRequest` | `RetrievalResponse` (Citations list) | Fully Working |
| `/api/upload/image` | POST | `UploadFile` (multipart) | `{ success: bool, image_path: str, filename: str }` | Fully Working |
| `/api/analyze/image` | POST | `UploadFile` (multipart) | `VisionAnalysisResponse` (modality, findings, impression) | Fully Working |

### 1.3 Patient Inputs & Output Schemas
- **Patient Case Inputs**: `patient_id` (string), `age` (int 0-150), `sex` (M/F/Other/Unknown), `symptoms` (comma-separated or string list), `history` (comma-separated or string list), `clinical_notes` (free text), `case_description` (string), `labs` (`list[LabResult]` with `name`, `value`, `unit`, `reference_range`, `is_abnormal`), `image_path` (optional path).
- **Agentic Analysis Output**: `case_id`, `iteration_count`, `agent_logs` (list of agent actions and timestamps), `image_findings` (findings list), `final_report`:
  1. `patient_summary`
  2. `key_clinical_findings`
  3. `imaging_findings` (`modality`, `technical_quality`, `model_used`, `overall_impression`, `findings`)
  4. `agent_assessments` (`general_physician`, `specialist`, `radiologist`)
  5. `differential_considerations` (`condition`, `uncertainty`, `supporting_evidence`, `contradicting_evidence`, `source_ids`)
  6. `evidence_citations` (`source_id`, `title`, `source`, `document_type`, `content`, `relevance_score`)
  7. `critic_findings` (`summary`, `supported_claims`, `unsupported_claims`, `missing_information`, `revision_required`)
  8. `suggested_next_questions`
  9. `safety_disclaimer`

---

## 2. Decision on Implementation: React + TypeScript + Tailwind CSS

### 2.1 Why Streamlit is Insufficient for Hospital-Grade Experience
- Streamlit forces full-page script re-runs on every user interaction, causing state resets, flickers, and latency.
- It cannot support a multi-page enterprise layout with responsive collapsible navigation, persistent patient header, multi-step clinical intake stepper, side-by-side radiology view with zoom/pan, or customizable high-density clinical data tables.
- Styling in Streamlit relies on fragile `st.markdown('<style>...', unsafe_allow_html=True)` hacks that break across Streamlit versions and cannot provide proper accessible keyboard navigation or modal dialogs.

### 2.2 Framework Decision
We will build a high-performance, modular React 19 / TypeScript / Vite application in `frontend/` styled with Tailwind CSS and Lucide React icons:
- Connects directly to the existing FastAPI backend (`http://localhost:8000/api`) with a robust central API client (`frontend/src/api/client.ts`).
- Fully preserves all existing backend code, agent workflows, and database tables.
- Retains `app.py` untouched so the Streamlit frontend remains available at all times.
- Adds a convenient `GET /api/cases` endpoint to FastAPI to populate the Clinical Overview dashboard and Patient Cases history with real SQLite database records.

---

## 3. Product Branding & Visual Design System

- **Product Name**: `ClinIQ Clinical Intelligence Workspace` (configurable via environment/settings).
- **Design Philosophy**: Clinical, trustworthy, high-density, accessible, distraction-free.
- **Palette**:
  - Background: Slate-50 / Cool White (`#f8fafc`, `#ffffff`)
  - Primary Typography: Deep Slate/Navy (`#0f172a`, `#1e293b`)
  - Primary Accent: Clinical Deep Teal / Slate Blue (`#0f766e`, `#0284c7`)
  - Borders: Refined neutral (`#e2e8f0`, `#cbd5e1`)
  - Status Accents:
    - Normal / Low Uncertainty: Emerald (`#059669`, `#ecfdf5`)
    - Moderate Uncertainty: Amber (`#d97706`, `#fffbeb`)
    - High Uncertainty / Urgent: Rose/Red (`#dc2626`, `#fef2f2`)
    - Neutral / Info: Sky/Slate (`#0284c7`, `#f0f9ff`)
- **Typography**: Inter / system sans-serif with strict scale (11px micro-labels, 13px tabular body, 14px form controls, 18px card headers, 24px page titles). Monospace for patient IDs, lab values, and citation tokens.
- **Iconography**: Unified Lucide React icons (no random emojis).

---

## 4. Application Architecture & Workspaces

### 4.1 Global Layout & Shell
- **Collapsible Clinical Sidebar**:
  - Brand header with ClinIQ icon, status dot, and collapse toggle.
  - Primary Navigation:
    1. Overview (`/overview`): System health, recent cases, quick actions, analytics.
    2. Patient Cases (`/cases`): Searchable, filterable case directory with status and timestamps.
    3. New Clinical Analysis (`/new-case`): 10-step guided clinical case intake stepper.
    4. Imaging (`/imaging`): Radiology workstation with scan upload, inspection, and vision findings.
    5. AI Analysis (`/workflow`): Live LangGraph agent topology, debate iterations, event logs.
    6. Evidence Library (`/evidence`): Knowledge base explorer, hybrid RAG query tool, citation cards.
    7. Reports (`/reports`): Formal 9-section Clinical Decision Support reports with Print/PDF export.
    8. System Settings (`/settings`): Configurable backend URL, LLM & Vision provider status, disclaimers.
  - Footer with backend connection indicator (latency ms, version, phase) and clinical disclaimer badge.

### 4.2 Patient Case Workspace (`/new-case`)
A 10-step structured clinical case form with breadcrumbs and direct step jumping:
1. Patient Demographics (ID, Age, Biological Sex).
2. Presenting Complaints (Symptoms with quick clinical tags).
3. Medical History & Comorbidities.
4. Current Medications (Structured list with dose/route).
5. Known Allergies.
6. Vital Signs (BP, Heart Rate, Respiratory Rate, SpO2, Temperature).
7. Laboratory Results (Predefined common panels + custom labs, reference ranges, abnormal flags).
8. Clinical Notes & Physical Examination.
9. Medical Imaging Attachment (Upload or attach demo radiograph).
10. Review & Submit (Summary preview, mode selection: Multi-Agent vs Baseline RAG, confirmation).

### 4.3 Imaging Workspace (`/imaging`)
- Clean split-screen radiology console.
- Left: Image upload dropzone, format validation (PNG, JPG, JPEG), synthetic demo CXR loader, metadata panel (file size, dimensions, modality).
- Right: High-resolution preview with zoom/fit toggles, vision service status (`MedicalVisionService`), structured visual findings table with anatomical locations and confidence levels, and technical quality notes.

### 4.4 Multi-Agent Analysis Workspace (`/workflow`)
- Visual agent execution topology graph:
  - `General Physician Agent` ➔ `Retrieval Agent` ➔ `Radiology Agent` ➔ `Specialist Agent` ➔ `Critic / Verifier` ➔ (Iterative loop back if revised) ➔ `Synthesizer`.
- Real backend execution state (Pending, Running, Completed, Failed).
- Debate iteration counter (e.g., `1 / 3 iterations`).
- Interactive step-by-step agent logs expander with tool invocations, hypotheses, and verification checks.

### 4.5 Evidence Explorer (`/evidence`)
- Two-tier layout:
  - Case Citations View: Filterable cards for active case evidence (`[E1]`, `[E2]`, etc.) showing document type, relevance score, source file, and extracted excerpt.
  - Interactive RAG Corpus Search: Standalone search bar triggering `/api/retrieve` to query the medical knowledge base with live results.

### 4.6 Final Clinical Report (`/reports`)
- Enterprise clinical document view formatted according to hospital report standards:
  - Header: Patient ID, timestamp, generating engine, clinical safety disclaimer.
  - Section 1: Patient Case Summary.
  - Section 2: Key Clinical Findings.
  - Section 3: Imaging Findings.
  - Section 4: Specialized Agent Assessments (GP, Specialist, Radiologist).
  - Section 5: Differential Considerations with uncertainty badges, supporting vs contradicting evidence, and evidence citation tags.
  - Section 6: Evidence Sources with relevance scores.
  - Section 7: Critic Verification (supported claims, unsupported claims, missing information).
  - Section 8: Suggested Next Clinical Questions for attending physician review.
  - Action Bar: Print report, Export JSON, Copy clinical text.

---

## 5. Implementation Steps & Verification

1. **Backend Extension**: Add `GET /api/cases` endpoint to `backend/api/routes.py` and `list_cases()` to `database/repository.py` to allow the frontend to display saved cases. Verify all 67 tests still pass.
2. **Frontend Project Setup**: Initialize Vite + React + TypeScript + Tailwind CSS in `frontend/`. Install Lucide React, classnames, and Axios.
3. **Design System & Components**: Build reusable UI primitives: `Button`, `Badge`, `Card`, `Modal`, `Input`, `Select`, `Table`, `Tabs`, `Alert`, `StatusDot`.
4. **API Client & State Management**: Implement `client.ts` with typed methods for all backend endpoints, error handling, and request timeout configurations.
5. **Views Implementation**:
   - `ClinicalOverview.tsx` (Dashboard)
   - `PatientWorkspace.tsx` (10-step intake)
   - `ImagingWorkspace.tsx` (Radiology viewer & findings)
   - `AgentWorkflow.tsx` (Multi-agent orchestration trace)
   - `EvidenceExplorer.tsx` (Corpus query & citations)
   - `ClinicalReport.tsx` (9-section CDS report with print layout)
   - `CasesList.tsx` (Saved patient directory)
   - `SettingsView.tsx` (Connection configuration)
6. **Integration & End-to-End Testing**: Run FastAPI backend on port 8000 and Vite dev server on port 3000/5173. Test end-to-end multi-agent analysis, image upload, demo case loading, and report printing.
7. **Documentation**: Update `README.md` with complete architecture notes, frontend and backend launch commands, and verification records.
