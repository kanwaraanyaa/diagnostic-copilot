"""
Streamlit frontend for the Diagnostic Copilot — Phase 2:
Multi-Agent Agentic RAG Diagnostic Copilot with Medical Image Analysis.
"""

from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image
import requests
import streamlit as st

# =============================================================================
# Configuration & Constants
# =============================================================================

BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
API_BASE = f"{BACKEND_URL}/api"

DISCLAIMER = (
    "⚠️ **FOR RESEARCH AND EDUCATIONAL USE ONLY.** "
    "This system is a research/educational clinical decision-support prototype and "
    "does not provide a confirmed medical diagnosis or replace a qualified healthcare professional."
)

COMMON_LABS = [
    {"name": "Hemoglobin", "unit": "g/dL", "reference_range": "12.0-17.5"},
    {"name": "WBC", "unit": "×10³/μL", "reference_range": "4.5-11.0"},
    {"name": "Platelets", "unit": "×10³/μL", "reference_range": "150-400"},
    {"name": "Glucose", "unit": "mg/dL", "reference_range": "70-100"},
    {"name": "Creatinine", "unit": "mg/dL", "reference_range": "0.6-1.3"},
    {"name": "CRP", "unit": "mg/L", "reference_range": "<10"},
    {"name": "Troponin", "unit": "ng/mL", "reference_range": "<0.04"},
]

DEMO_IMAGE_PATH = "data/demo/demo_chest_xray.png"

DEMO_CASE = {
    "patient_id": "PT-DEMO-2026",
    "age": 45,
    "sex": "M",
    "symptoms": "fever, cough, shortness of breath, fatigue",
    "history": "hypertension, type 2 diabetes",
    "clinical_notes": (
        "Patient presents with 3-day history of productive cough with yellowish sputum, "
        "fever up to 38.9°C, and progressive shortness of breath. Auscultation reveals "
        "crackles over the right lower lung base. Mild pleuritic discomfort on deep inspiration."
    ),
    "labs": [
        {"name": "WBC", "value": 14.5, "unit": "×10³/μL", "reference_range": "4.5-11.0", "is_abnormal": True},
        {"name": "CRP", "value": 85.0, "unit": "mg/L", "reference_range": "<10", "is_abnormal": True},
        {"name": "Hemoglobin", "value": 13.2, "unit": "g/dL", "reference_range": "12.0-17.5", "is_abnormal": False},
        {"name": "Glucose", "value": 145.0, "unit": "mg/dL", "reference_range": "70-100", "is_abnormal": True},
        {"name": "Creatinine", "value": 1.1, "unit": "mg/dL", "reference_range": "0.6-1.3", "is_abnormal": False},
    ],
    "image_path": DEMO_IMAGE_PATH if os.path.exists(DEMO_IMAGE_PATH) else None,
}


# =============================================================================
# Streamlit Page Config & Styling
# =============================================================================

st.set_page_config(
    page_title="Diagnostic Copilot — Multi-Agent RAG",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

    /* Disclaimer banner */
    .disclaimer-banner {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(245, 158, 11, 0.15));
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 8px;
        padding: 12px 18px;
        margin-bottom: 20px;
        font-size: 0.88rem;
        color: #fca5a5;
    }

    /* Workflow node cards */
    .workflow-card {
        background-color: #1e1e2f;
        border: 1px solid #3d3d5c;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 12px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .workflow-card:hover {
        border-color: #6366f1;
        transform: translateY(-2px);
    }
    .workflow-card-active {
        border-color: #10b981;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.25);
    }

    /* Evidence badge */
    .evidence-badge {
        display: inline-block;
        background: #2d2d4e;
        border: 1px solid #6366f1;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.78rem;
        color: #a5b4fc;
        margin: 2px;
    }

    /* Uncertainty indicators */
    .uncertainty-low { color: #34d399; font-weight: 600; }
    .uncertainty-moderate { color: #fbbf24; font-weight: 600; }
    .uncertainty-high { color: #f87171; font-weight: 600; }
    .uncertainty-unknown { color: #9ca3af; font-weight: 600; }

    /* Metric pill */
    .metric-pill {
        display: inline-block;
        background: #262638;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.82rem;
        margin-right: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# Helper Functions
# =============================================================================

def call_api(
    endpoint: str,
    method: str = "POST",
    payload: dict | None = None,
    files: dict | None = None,
) -> dict | None:
    """Make an HTTP call to the FastAPI backend."""
    url = f"{API_BASE}/{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, timeout=120)
        elif files:
            resp = requests.post(url, files=files, timeout=120)
        else:
            resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(
            "❌ **Cannot connect to backend.** Please ensure the FastAPI server is running:\n\n"
            "```bash\nuvicorn backend.main:app --reload\n```"
        )
        return None
    except Exception as e:
        st.error(f"⚠️ API Error ({endpoint}): {e}")
        return None


def render_uncertainty(level: str) -> str:
    """Format uncertainty level with color and icon."""
    lvl = (level or "unknown").lower()
    mapping = {
        "low": ("🟢", "uncertainty-low", "Low Uncertainty"),
        "moderate": ("🟡", "uncertainty-moderate", "Moderate Uncertainty"),
        "high": ("🔴", "uncertainty-high", "High Uncertainty"),
        "unknown": ("⚪", "uncertainty-unknown", "Unspecified Uncertainty"),
    }
    icon, css, label = mapping.get(lvl, mapping["unknown"])
    return f'{icon} <span class="{css}">{label}</span>'


# =============================================================================
# Sidebar
# =============================================================================

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/medical-doctor.png", width=64)
    st.title("🏥 Diagnostic Copilot")
    st.caption("Phase 2 — Multi-Agent System + Medical Vision")

    st.divider()

    # Backend Health Check
    health = call_api("health", method="GET")
    if health:
        phase_label = f"Phase {health.get('phase', 2)}"
        st.success(f"✅ Backend online — v{health.get('version', '0.2.0')} ({phase_label})")
    else:
        st.warning("⚠️ Backend offline")

    st.divider()

    # Execution Mode
    mode = st.radio(
        "🧠 Analysis Engine:",
        ["Multi-Agent Workflow (Phase 2)", "Single-Shot Baseline RAG (Phase 1)"],
        index=0,
    )
    st.session_state["analysis_mode"] = mode

    st.divider()

    if st.button("📋 Load Demo Case & CXR", use_container_width=True):
        st.session_state["demo_loaded"] = True
        st.session_state["labs"] = list(DEMO_CASE["labs"])
        if os.path.exists(DEMO_IMAGE_PATH):
            st.session_state["active_image_path"] = DEMO_IMAGE_PATH
        st.rerun()

    if st.button("🗑️ Reset Session", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    st.divider()
    st.markdown(f'<div class="disclaimer-banner">{DISCLAIMER}</div>', unsafe_allow_html=True)


# =============================================================================
# Main Application Tabs
# =============================================================================

st.markdown(f'<div class="disclaimer-banner">{DISCLAIMER}</div>', unsafe_allow_html=True)

tab_patient, tab_image, tab_workflow, tab_evidence, tab_report, tab_phase3 = st.tabs([
    "📝 Patient Input",
    "🩻 Medical Image",
    "🤖 Agent Workflow",
    "📚 Evidence",
    "📋 Final Report",
    "🔬 Phase 3: Evaluation & Ablation",
])

# Initialize session defaults
demo_data = DEMO_CASE if st.session_state.get("demo_loaded") else {}
if "labs" not in st.session_state:
    st.session_state["labs"] = list(demo_data.get("labs", []))


# -----------------------------------------------------------------------------
# TAB 1: Patient Input
# -----------------------------------------------------------------------------
with tab_patient:
    st.header("Patient Case Presentation")

    col_info1, col_info2 = st.columns([3, 1])
    with col_info1:
        st.caption("Enter patient demographics, history, laboratory values, and clinical observations.")
    with col_info2:
        if st.session_state.get("demo_loaded"):
            st.info("Demo case loaded. Modify values as needed.")

    col_dem1, col_dem2, col_dem3 = st.columns(3)
    with col_dem1:
        patient_id = st.text_input("Patient Identifier", value=demo_data.get("patient_id", "PT-10492"))
    with col_dem2:
        age = st.number_input("Age (years)", min_value=0, max_value=150, value=demo_data.get("age", 45), step=1)
    with col_dem3:
        sex_options = ["Unknown", "M", "F", "Other"]
        def_idx = sex_options.index(demo_data.get("sex", "M")) if demo_data.get("sex") in sex_options else 0
        sex = st.selectbox("Biological Sex", sex_options, index=def_idx)

    col_sym, col_hist = st.columns(2)
    with col_sym:
        symptoms = st.text_area(
            "Symptoms (comma-separated)",
            value=demo_data.get("symptoms", ""),
            height=90,
            placeholder="e.g. fever, productive cough, dyspnea",
        )
    with col_hist:
        history = st.text_area(
            "Medical History / Comorbidities",
            value=demo_data.get("history", ""),
            height=90,
            placeholder="e.g. hypertension, type 2 diabetes, asthma",
        )

    clinical_notes = st.text_area(
        "Clinical Notes & Physical Examination",
        value=demo_data.get("clinical_notes", ""),
        height=110,
        placeholder="Physical exam observations, auscultation findings, onset timeline...",
    )

    # Dynamic Labs Section
    st.subheader("🧪 Laboratory Findings")
    st.caption("Quick add common tests or enter custom values:")

    quick_cols = st.columns(len(COMMON_LABS))
    for i, lab_t in enumerate(COMMON_LABS):
        with quick_cols[i]:
            if st.button(lab_t["name"], key=f"btn_add_{lab_t['name']}", use_container_width=True):
                existing_names = [l["name"] for l in st.session_state["labs"]]
                if lab_t["name"] not in existing_names:
                    st.session_state["labs"].append({
                        "name": lab_t["name"],
                        "value": 0.0,
                        "unit": lab_t["unit"],
                        "reference_range": lab_t["reference_range"],
                        "is_abnormal": False,
                    })
                    st.rerun()

    # Existing lab entries
    for idx, lab in enumerate(st.session_state["labs"]):
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([2.5, 1.5, 1.2, 1.8, 0.8])
            with c1:
                lab["name"] = st.text_input("Test", value=lab.get("name", ""), key=f"lab_n_{idx}")
            with c2:
                lab["value"] = st.number_input("Value", value=float(lab.get("value", 0.0)), key=f"lab_v_{idx}", format="%.2f")
            with c3:
                lab["unit"] = st.text_input("Unit", value=lab.get("unit", ""), key=f"lab_u_{idx}")
            with c4:
                lab["reference_range"] = st.text_input("Ref Range", value=lab.get("reference_range", ""), key=f"lab_r_{idx}")
            with c5:
                lab["is_abnormal"] = st.checkbox("Abn", value=bool(lab.get("is_abnormal", False)), key=f"lab_a_{idx}")

    c_btn1, c_btn2 = st.columns([1, 4])
    with c_btn1:
        if st.button("➕ Custom Lab"):
            st.session_state["labs"].append({"name": "", "value": 0.0, "unit": "", "reference_range": "", "is_abnormal": False})
            st.rerun()
    with c_btn2:
        if st.button("🗑️ Clear Labs"):
            st.session_state["labs"] = []
            st.rerun()

    st.divider()

    # Image attachment indicator
    active_img = st.session_state.get("active_image_path")
    if active_img:
        st.info(f"🩻 **Attached Medical Image:** `{os.path.basename(active_img)}` (configured in the 'Medical Image' tab)")
    else:
        st.caption("ℹ️ No medical image attached yet. You can attach one in the **Medical Image** tab.")

    # Execution Trigger
    if st.button("🚀 Run Multi-Agent Diagnostic Analysis", type="primary", use_container_width=True):
        if not symptoms.strip() and not clinical_notes.strip():
            st.warning("Please provide patient symptoms or clinical notes before running analysis.")
        else:
            payload = {
                "patient_id": patient_id,
                "age": age if age > 0 else None,
                "sex": sex,
                "symptoms": symptoms,
                "history": history,
                "clinical_notes": clinical_notes,
                "case_description": "",
                "labs": [l for l in st.session_state.get("labs", []) if l.get("name")],
                "image_path": active_img,
            }

            mode_selected = st.session_state.get("analysis_mode", "Multi-Agent Workflow (Phase 2)")

            if "Multi-Agent" in mode_selected:
                with st.spinner("🤖 Orchestrating multi-agent workflow (GP ➔ Retrieval ➔ Specialist ➔ Radiologist ➔ Critic ➔ Synthesizer)..."):
                    res = call_api("analyze/agentic", payload=payload)
                    if res and res.get("success"):
                        st.session_state["agentic_result"] = res
                        st.session_state["analysis_result"] = None  # Clear old phase 1
                        st.success("✅ Multi-agent diagnostic copilot completed! Check the **Agent Workflow** and **Final Report** tabs.")
                    elif res:
                        st.error(f"Analysis error: {res.get('error', 'Unknown failure')}")
            else:
                with st.spinner("🔬 Running baseline Phase 1 RAG pipeline..."):
                    res = call_api("analyze", payload=payload)
                    if res and res.get("success"):
                        st.session_state["analysis_result"] = res
                        st.session_state["agentic_result"] = None
                        st.success("✅ Baseline RAG analysis completed! View results in the **Final Report** tab.")
                    elif res:
                        st.error(f"Analysis error: {res.get('error', 'Unknown failure')}")


# -----------------------------------------------------------------------------
# TAB 2: Medical Image
# -----------------------------------------------------------------------------
with tab_image:
    st.header("🩻 Medical Image Upload & Radiology Analysis")
    st.caption("Upload patient radiography (Chest X-ray PNG/JPG) or use the synthetic clinical demo scan.")

    col_img_up, col_img_view = st.columns([1, 1])

    with col_img_up:
        uploaded_file = st.file_uploader(
            "Upload Chest X-ray (PNG or JPG)",
            type=["png", "jpg", "jpeg"],
            help="Images are preprocessed, sanitized, and evaluated with clinical vision adapters.",
        )

        if uploaded_file is not None:
            # Upload to backend
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            up_res = call_api("upload/image", files=files)
            if up_res and up_res.get("success"):
                st.session_state["active_image_path"] = up_res.get("image_path")
                st.session_state["uploaded_image_bytes"] = uploaded_file.getvalue()
                st.success(f"✅ Uploaded `{uploaded_file.name}` successfully.")

        st.markdown("---")
        st.subheader("Synthetic Demo Scan")
        if os.path.exists(DEMO_IMAGE_PATH):
            if st.button("🖼️ Attach Synthetic Demo Chest X-ray"):
                st.session_state["active_image_path"] = DEMO_IMAGE_PATH
                st.session_state["uploaded_image_bytes"] = None
                st.success("Attached demo chest radiograph.")
                st.rerun()

        if st.button("🔍 Run Standalone Vision Analysis", use_container_width=True):
            img_to_analyze = st.session_state.get("active_image_path")
            if not img_to_analyze or not os.path.exists(img_to_analyze):
                st.warning("Please upload or attach an image first.")
            else:
                with st.spinner("Analyzing image via MedicalVisionService..."):
                    with open(img_to_analyze, "rb") as f:
                        v_files = {"file": (os.path.basename(img_to_analyze), f.read(), "image/png")}
                    v_res = call_api("analyze/image", files=v_files)
                    if v_res and v_res.get("success"):
                        st.session_state["standalone_vision"] = v_res
                        st.success("Vision analysis complete.")

    with col_img_view:
        active_img_path = st.session_state.get("active_image_path")
        if active_img_path and os.path.exists(active_img_path):
            st.subheader("Image Preview")
            img_obj = Image.open(active_img_path)
            st.image(img_obj, caption=f"Active scan: {os.path.basename(active_img_path)} ({img_obj.size[0]}x{img_obj.size[1]})", width=380)

            # Metadata details
            st.markdown(
                f'<span class="metric-pill">Modality: Chest Radiograph</span>'
                f'<span class="metric-pill">Format: {img_obj.format or "PNG"}</span>'
                f'<span class="metric-pill">Dimensions: {img_obj.size[0]}×{img_obj.size[1]}</span>',
                unsafe_allow_html=True,
            )
        else:
            st.info("No active image selected. Upload a file or load the demo image.")

    # Vision results display
    vision_data = st.session_state.get("standalone_vision")
    if vision_data and vision_data.get("success"):
        st.divider()
        st.subheader("🔬 Radiology Vision Findings")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.markdown(f"**Modality:** {vision_data.get('image_modality', 'Radiograph')}")
            st.markdown(f"**Technical Quality:** {vision_data.get('technical_quality', 'Adequate').title()}")
            st.markdown(f"**Vision Model:** `{vision_data.get('model_used', 'LocalDemoVisionAdapter')}`")
        with col_v2:
            st.markdown(f"**Impression:** {vision_data.get('overall_impression', 'No impression available.')}")

        findings = vision_data.get("findings", [])
        if findings:
            st.markdown("#### Detected Visual Features:")
            for f in findings:
                with st.expander(f"📍 {f.get('location', 'Anatomical region')}: {f.get('finding', 'Finding')}", expanded=True):
                    st.markdown(render_uncertainty(f.get("confidence", "moderate")), unsafe_allow_html=True)
                    st.caption(f"Source: `{f.get('source', 'vision_model')}`")


# -----------------------------------------------------------------------------
# TAB 3: Agent Workflow
# -----------------------------------------------------------------------------
with tab_workflow:
    st.header("🤖 Multi-Agent LangGraph Workflow Orchestration")
    st.caption("Visual execution trace of specialized clinical AI agents collaborating under iterative debate.")

    agentic_res = st.session_state.get("agentic_result")

    # Workflow topology representation
    st.subheader("Agent Architecture & State Flow")
    wf_cols = st.columns(6)

    nodes = [
        ("GP Agent", "🩺 General Physician", "Case triage & hypothesis formulation"),
        ("Retrieval Agent", "🔍 RAG Search", "Medical evidence retrieval & citations"),
        ("Specialist Agent", "🫀 Specialist", "Cardiopulmonary deep clinical assessment"),
        ("Radiology Agent", "🩻 Radiologist", "Vision findings & radiographic analysis"),
        ("Critic Agent", "⚖️ Critic / Verifier", "Claim verification & contradiction check"),
        ("Final Synthesizer", "📑 Synthesizer", "Compiles 9-section clinical decision report"),
    ]

    has_run = agentic_res is not None

    for i, (name, icon, desc) in enumerate(nodes):
        with wf_cols[i]:
            card_class = "workflow-card-active" if has_run else "workflow-card"
            st.markdown(
                f"""
                <div class="workflow-card {card_class}">
                    <div style="font-size: 1.1rem; font-weight: 600;">{icon}</div>
                    <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">{desc}</div>
                    <div style="margin-top: 8px;">
                        {'<span style="color:#10b981; font-size:0.75rem;">● Completed</span>' if has_run else '<span style="color:#64748b; font-size:0.75rem;">○ Ready</span>'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if not agentic_res:
        st.info("👈 Run a diagnostic analysis from the **Patient Input** tab to visualize agent collaboration and activity logs.")
    else:
        st.divider()
        st.subheader("Workflow Execution Metrics")
        m1, m2, m3 = st.columns(3)
        m1.metric("Debate Iterations", f"{agentic_res.get('iteration_count', 1)} / 3 max")
        m2.metric("Agent Events Logged", len(agentic_res.get("agent_logs", [])))
        m3.metric("Imaging Analyzed", "Yes" if agentic_res.get("image_findings") else "No")

        st.subheader("Agent Execution Trace")
        logs = agentic_res.get("agent_logs", [])
        if logs:
            for idx, log_item in enumerate(logs):
                agent_name = log_item.get("agent", "Agent")
                action_text = log_item.get("action", "")
                with st.expander(f"Step {idx+1}: {agent_name} — {action_text[:70]}...", expanded=(idx == len(logs)-1)):
                    st.write(f"**Agent:** {agent_name}")
                    st.write(f"**Action:** {action_text}")
                    details = {k: v for k, v in log_item.items() if k not in ("agent", "action")}
                    if details:
                        st.json(details)


# -----------------------------------------------------------------------------
# TAB 4: Evidence
# -----------------------------------------------------------------------------
with tab_evidence:
    st.header("📚 Retrieved Medical Evidence & Knowledge Base")
    st.caption("Evidence passages retrieved via Hybrid Search (Dense embeddings + BM25 sparse index + Cross-Encoder reranking).")

    report_evidence = None
    if st.session_state.get("agentic_result"):
        report_evidence = st.session_state["agentic_result"].get("final_report", {}).get("evidence_citations", [])
    elif st.session_state.get("analysis_result"):
        report_evidence = st.session_state["analysis_result"].get("report", {}).get("citations", [])

    if report_evidence:
        st.subheader(f"Evidence Cited in Case ({len(report_evidence)} sources)")
        for cit in report_evidence:
            with st.expander(f"[{cit.get('source_id', 'E?')}] {cit.get('title', 'Clinical Guideline')} — Score: {cit.get('relevance_score', 0):.2f}", expanded=True):
                st.markdown(f"**Document Type:** `{cit.get('document_type', 'clinical_guideline')}`")
                st.markdown(f"**Source Document:** `{cit.get('source', 'local_corpus')}`")
                st.divider()
                st.markdown(cit.get("content", "No content snippet."))
    else:
        st.info("No active analysis evidence available yet. Submit a case in the Patient Input tab.")

    st.divider()
    st.subheader("🔍 Interactive Evidence Search")
    st.caption("Query the local clinical knowledge base directly using Hybrid RAG.")

    q_col, b_col = st.columns([4, 1])
    with q_col:
        manual_q = st.text_input("Query clinical corpus:", placeholder="e.g. community acquired pneumonia CURB-65 criteria")
    with b_col:
        st.write("")
        search_clicked = st.button("Search KB", use_container_width=True)

    if search_clicked and manual_q.strip():
        with st.spinner("Executing hybrid retrieval..."):
            ret_res = call_api("retrieve", payload={"query": manual_q, "top_k": 5})
            if ret_res and ret_res.get("success"):
                results = ret_res.get("results", [])
                st.success(f"Retrieved {len(results)} relevant passages:")
                for r in results:
                    with st.expander(f"[{r.get('source_id')}] {r.get('title')} (Score: {r.get('relevance_score', 0):.2f})"):
                        st.markdown(f"**Type:** `{r.get('document_type')}` | **File:** `{r.get('source')}`")
                        st.markdown(r.get("content", ""))
            elif ret_res:
                st.error(ret_res.get("error", "Search failed."))


# -----------------------------------------------------------------------------
# TAB 5: Final Report
# -----------------------------------------------------------------------------
with tab_report:
    st.header("📋 Clinical Decision Support Report")

    agentic_data = st.session_state.get("agentic_result")
    baseline_data = st.session_state.get("analysis_result")

    if not agentic_data and not baseline_data:
        st.info("👈 Run an analysis from the **Patient Input** tab to generate the full Clinical Decision Support Report.")
    elif agentic_data and agentic_data.get("success"):
        rep = agentic_data.get("final_report", {})

        # Safety Banner (Section 9)
        st.markdown(
            f'<div class="disclaimer-banner">{rep.get("safety_disclaimer", DISCLAIMER)}</div>',
            unsafe_allow_html=True,
        )

        # 1. Patient Summary
        st.subheader("1. 👤 Patient Summary")
        st.write(rep.get("patient_summary", "Summary not available."))

        # 2. Key Clinical Findings
        st.subheader("2. 🔎 Key Clinical Findings")
        findings = rep.get("key_clinical_findings", [])
        if findings:
            for f in findings:
                st.markdown(f"- {f}")
        else:
            st.caption("No specific positive findings noted.")

        # 3. Imaging Findings
        st.subheader("3. 🩻 Imaging Findings")
        img_sec = rep.get("imaging_findings", {})
        col_img1, col_img2 = st.columns(2)
        with col_img1:
            st.markdown(f"**Modality:** {img_sec.get('modality', 'None')}")
            st.markdown(f"**Technical Quality:** {img_sec.get('technical_quality', 'N/A')}")
            st.markdown(f"**Model Used:** `{img_sec.get('model_used', 'N/A')}`")
        with col_img2:
            st.markdown(f"**Impression:** {img_sec.get('overall_impression', 'N/A')}")

        img_list = img_sec.get("findings", [])
        if img_list:
            st.markdown("**Specific Visual Findings:**")
            for item in img_list:
                st.markdown(f"- **{item.get('location', 'Region')}:** {item.get('finding')} (Confidence: {item.get('confidence', 'moderate')})")

        # 4. Agent Assessments
        st.subheader("4. 🧑‍⚕️ Specialized Agent Assessments")
        assessments = rep.get("agent_assessments", {})

        col_gp, col_sp, col_rad = st.columns(3)
        with col_gp:
            st.markdown("##### General Physician")
            gp_data = assessments.get("general_physician", {})
            st.caption(gp_data.get("patient_summary", "GP initial assessment completed."))
            hyps = gp_data.get("initial_hypotheses", [])
            if hyps:
                for h in hyps:
                    st.markdown(f"- **{h.get('condition')}**: {h.get('clinical_rationale')}")

        with col_sp:
            st.markdown("##### Specialist (Cardiopulmonary)")
            sp_data = assessments.get("specialist", {})
            st.markdown(f"**Assessment:** {sp_data.get('specialist_assessment', 'Specialist review completed.')}")
            recs = sp_data.get("diagnostic_recommendations", [])
            if recs:
                st.markdown("**Recommendations:**")
                for r in recs:
                    st.markdown(f"- {r}")

        with col_rad:
            st.markdown("##### Radiologist")
            rad_data = assessments.get("radiologist", {})
            st.markdown(f"**Interpretation:** {rad_data.get('overall_impression', 'Radiology evaluated.')}")

        # 5. Differential Considerations
        st.subheader("5. 🩺 Differential Considerations")
        st.caption("Differential considerations synthesized from clinical data, evidence, and imaging findings. These are NOT diagnoses.")

        diffs = rep.get("differential_considerations", [])
        if diffs:
            for i, diff in enumerate(diffs):
                cond_name = diff.get("condition", "Clinical Syndrome")
                uncert = diff.get("uncertainty", "moderate")
                with st.expander(f"**{cond_name}** — {uncert.title()} Uncertainty", expanded=(i == 0)):
                    st.markdown(render_uncertainty(uncert), unsafe_allow_html=True)

                    c_sup, c_contra = st.columns(2)
                    with c_sup:
                        st.markdown("**✅ Supporting Evidence:**")
                        sup_list = diff.get("supporting_evidence", [])
                        if sup_list:
                            for item in sup_list:
                                st.markdown(f"- {item}")
                        else:
                            st.caption("None reported.")

                    with c_contra:
                        st.markdown("**❌ Contradicting / Absent Evidence:**")
                        contra_list = diff.get("contradicting_evidence", [])
                        if contra_list:
                            for item in contra_list:
                                st.markdown(f"- {item}")
                        else:
                            st.caption("None reported.")

                    sids = diff.get("source_ids", [])
                    if sids:
                        badge_html = " ".join(f'<span class="evidence-badge">{s}</span>' for s in sids)
                        st.markdown(f"**Evidence Citations:** {badge_html}", unsafe_allow_html=True)

        # 6. Evidence Citation Summary
        st.subheader("6. 📚 Evidence Sources")
        cits = rep.get("evidence_citations", [])
        if cits:
            for cit in cits:
                st.markdown(f"- **[{cit.get('source_id')}]** *{cit.get('title')}* — `{cit.get('source')}` (Score: {cit.get('relevance_score', 0):.2f})")

        # 7. Critic Findings
        st.subheader("7. ⚖️ Critic / Verifier Findings")
        critic = rep.get("critic_findings", {})
        st.markdown(f"**Verification Summary:** {critic.get('summary', 'Audit complete.')}")

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("**Supported Claims:**")
            for c in critic.get("supported_claims", []):
                st.markdown(f"- ✅ {c}")
            if not critic.get("supported_claims"):
                st.caption("No supported claims listed.")

        with col_c2:
            st.markdown("**Audit Flags & Missing Evidence:**")
            for c in critic.get("unsupported_claims", []):
                st.markdown(f"- ⚠️ *Unsupported:* {c}")
            for m in critic.get("missing_information", []):
                st.markdown(f"- ℹ️ *Missing:* {m}")

        # 8. Suggested Next Clinical Questions
        st.subheader("8. ❓ Suggested Next Clinical Questions")
        questions = rep.get("suggested_next_questions", [])
        if questions:
            for q in questions:
                st.markdown(f"- {q}")

        # 9. Safety Disclaimer (Repeated at footer)
        st.divider()
        st.caption(f"🔒 {rep.get('safety_disclaimer', DISCLAIMER)}")

        # Download Report Option
        st.download_button(
            "📥 Download Report as JSON",
            data=json.dumps(rep, indent=2),
            file_name=f"clinical_report_{agentic_data.get('case_id', 'case')}.json",
            mime="application/json",
            use_container_width=True,
        )

    elif baseline_data and baseline_data.get("success"):
        # Fallback view for baseline Phase 1 run
        b_rep = baseline_data.get("report", {})
        st.info("Showing Phase 1 Baseline RAG report.")
        st.subheader("Patient Summary")
        st.write(b_rep.get("patient_summary", ""))
        st.subheader("Differential Considerations")
        for d in b_rep.get("differential_considerations", []):
            st.write(f"- **{d.get('condition')}**: {d.get('uncertainty')}")


# -----------------------------------------------------------------------------
# TAB 6: Phase 3 Research, Benchmarks & Ablation
# -----------------------------------------------------------------------------
with tab_phase3:
    st.header("🔬 Phase 3: Advanced Agentic RAG & Evaluation Laboratory")
    st.caption("Empirical benchmarking across 50 clinical cases, ablation studies, evidence graphs, and hallucination auditing.")

    eval_subtab1, eval_subtab2, eval_subtab3 = st.tabs([
        "📊 50-Case Benchmark Suite",
        "⚖️ Architectural Ablation Matrix",
        "🕸️ Evidence Knowledge Graph & Similar Cohort",
    ])

    with eval_subtab1:
        st.subheader("Gold-Standard Clinical Evaluation Benchmark")
        st.caption("Evaluates diagnostic accuracy, differential recall, and critical rule-out identification across 50 internal medicine encounters.")

        col_b1, col_b2 = st.columns([3, 1])
        with col_b1:
            bm_count = st.slider("Benchmark Cases to Evaluate:", min_value=5, max_value=50, value=10, step=5)
        with col_b2:
            st.write("")
            run_bm_btn = st.button("▶️ Execute Benchmark", type="primary", use_container_width=True)

        if run_bm_btn:
            with st.spinner(f"Running automated multi-agent evaluation across {bm_count} clinical benchmark cases..."):
                try:
                    from evaluation.benchmark_runner import run_benchmark_suite
                    bm_result = run_benchmark_suite(max_cases=bm_count)
                    st.session_state["st_bm_result"] = bm_result.model_dump()
                    st.success(f"Benchmark completed successfully for {bm_result.total_cases_evaluated} cases!")
                except Exception as e:
                    st.error(f"Benchmark execution failed: {e}")

        # Display latest results
        saved_bm = st.session_state.get("st_bm_result")
        if not saved_bm:
            # Try loading from disk
            bm_path = os.path.join("data", "evaluation", "benchmark_results.json")
            if os.path.exists(bm_path):
                try:
                    with open(bm_path, "r", encoding="utf-8") as f:
                        saved_bm = json.load(f)
                except Exception:
                    pass

        if saved_bm:
            st.divider()
            st.subheader(f"Evaluation Metrics ({saved_bm.get('total_cases_evaluated', 0)} Cases)")
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Top-1 Accuracy", f"{saved_bm.get('top_1_accuracy', 0)}%")
            k2.metric("Top-3 Inclusion", f"{saved_bm.get('top_3_accuracy', 0)}%")
            k3.metric("Rule-Out Recall", f"{saved_bm.get('critical_rule_out_recall', 0)}%")
            k4.metric("Faithfulness", f"{saved_bm.get('mean_faithfulness_score', 0)}%")
            k5.metric("Mean Latency", f"{saved_bm.get('mean_latency_seconds', 0)}s")

            st.divider()
            st.subheader("Case-by-Case Diagnostic Evaluation Matrix")
            case_rows = []
            for cd in saved_bm.get("case_details", []):
                case_rows.append({
                    "Case ID": cd.get("case_id"),
                    "Category": cd.get("category"),
                    "Gold-Standard Diagnosis": cd.get("gold_standard_primary"),
                    "Model Top Differential": cd.get("top_1_differential"),
                    "Top-1 Hit": "✅ Yes" if cd.get("top_1_match") else "❌ No",
                    "Top-3 Hit": "✅ Yes" if cd.get("top_3_match") else "❌ No",
                    "Rule-Out Recall": f"{cd.get('rule_out_recall')}%",
                    "Faithfulness": f"{cd.get('faithfulness_score')}%",
                    "Latency": f"{cd.get('latency_seconds')}s",
                })
            if case_rows:
                st.dataframe(case_rows, use_container_width=True)

    with eval_subtab2:
        st.subheader("System Architecture Ablation Matrix")
        st.caption("Compares the proposed ClinIQ multi-agent architecture against single-agent RAG, no-debate, and dense-only variants.")

        if st.button("🧪 Execute Ablation Study (5 Variants)", use_container_width=True):
            with st.spinner("Running comparative ablation experiments..."):
                try:
                    from evaluation.ablation import run_ablation_study
                    ab_res = run_ablation_study(max_cases=5)
                    st.session_state["st_ab_result"] = ab_res.model_dump()
                    st.success("Ablation study completed!")
                except Exception as e:
                    st.error(f"Ablation study failed: {e}")

        saved_ab = st.session_state.get("st_ab_result")
        if not saved_ab:
            ab_path = os.path.join("data", "evaluation", "ablation_results.json")
            if os.path.exists(ab_path):
                try:
                    with open(ab_path, "r", encoding="utf-8") as f:
                        saved_ab = json.load(f)
                except Exception:
                    pass

        if saved_ab:
            st.divider()
            ab_rows = []
            for v in saved_ab.get("variants", []):
                ab_rows.append({
                    "Architecture Variant": v.get("variant_name"),
                    "Top-1 Accuracy": f"{v.get('top_1_accuracy')}%",
                    "Top-3 Recall": f"{v.get('top_3_accuracy')}%",
                    "Rule-Out Recall": f"{v.get('critical_rule_out_recall')}%",
                    "Faithfulness": f"{v.get('faithfulness_score')}%",
                    "Hallucination Rate": f"{v.get('hallucination_rate')}%",
                    "Mean Latency": f"{v.get('mean_latency_seconds')}s",
                })
            st.dataframe(ab_rows, use_container_width=True)
            st.info(f"💡 **Takeaway:** {saved_ab.get('comparative_summary', '')}")

    with eval_subtab3:
        st.subheader("Clinical Evidence Knowledge Graph & CBR Cohort")
        st.caption("Relational reasoning connections and matching patient encounters.")

        eg_c1, eg_c2 = st.columns(2)
        with eg_c1:
            st.markdown("#### Similar Patient Cohort (CBR)")
            try:
                from patient.similar_patients import get_reference_cohort
                cohort = get_reference_cohort()
                st.write(f"Reference cohort contains **{len(cohort)}** gold-standard reference patient profiles.")
                for ref in cohort[:3]:
                    with st.expander(f"{ref.case_id}: {ref.confirmed_diagnosis}"):
                        st.write(f"**Outcome:** {ref.clinical_outcome}")
                        st.write(f"**Takeaway:** {ref.clinical_takeaway}")
            except Exception as e:
                st.write(f"Cohort loader: {e}")

        with eg_c2:
            st.markdown("#### Evidence Graph Engine")
            st.write("Generates directed evidence graphs connecting findings, candidate hypotheses, and citations.")
            st.markdown("- **Finding Nodes:** Presenting symptoms, vital signs, lab abnormalities, imaging opacities.")
            st.markdown("- **Hypothesis Nodes:** Diagnostic differential considerations with net support scoring.")
            st.markdown("- **Evidence Nodes:** Peer-reviewed literature and guideline citations (`[E1]`, `[E2]`).")
            st.markdown("- **Edge Relations:** `SUPPORTS`, `CONTRADICTS`, `CITES`, `OBSERVES`.")

