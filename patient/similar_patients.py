"""
Similar Patient Retrieval — Phase 3.
Case-Based Reasoning (CBR) module for clinical decision support.
Finds clinically similar historical or reference cohort cases using a composite
scoring function (symptom Jaccard overlap, biomarker pattern correlation, and demographic alignment).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from config import get_settings
from logger import get_logger

log = get_logger(__name__)


class ReferenceCase(BaseModel):
    """A reference patient case in the historical cohort."""
    case_id: str
    age: int
    sex: str
    symptoms: list[str]
    history: list[str]
    labs: list[dict[str, Any]]
    confirmed_diagnosis: str
    clinical_outcome: str
    discriminant_features: list[str]
    clinical_takeaway: str


class SimilarPatientMatch(BaseModel):
    """A match result between active patient and a reference case."""
    case_id: str
    age: int
    sex: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)  # 0.0 to 1.0 (or 0-100%)
    symptom_similarity: float = 0.0
    lab_similarity: float = 0.0
    demographic_similarity: float = 0.0
    confirmed_diagnosis: str
    clinical_outcome: str
    matched_symptoms: list[str] = Field(default_factory=list)
    key_discriminant_pearls: list[str] = Field(default_factory=list)
    clinical_takeaway: str


class SimilarPatientResponse(BaseModel):
    """Overall response containing top similar patient matches."""
    query_case_id: str = ""
    matches: list[SimilarPatientMatch] = Field(default_factory=list)
    cohort_size: int = 0
    clinical_summary: str = ""


# Default built-in benchmark reference cohort spanning common internal medicine encounters
DEFAULT_COHORT: list[dict[str, Any]] = [
    {
        "case_id": "REF-PNEUM-01",
        "age": 48,
        "sex": "M",
        "symptoms": ["productive cough", "fever", "chills", "pleuritic chest pain", "dyspnea"],
        "history": ["hypertension", "former smoker"],
        "labs": [
            {"name": "WBC", "value": 16.4, "unit": "10^3/uL", "is_abnormal": True},
            {"name": "CRP", "value": 115.0, "unit": "mg/L", "is_abnormal": True},
            {"name": "Procalcitonin", "value": 1.8, "unit": "ng/mL", "is_abnormal": True},
        ],
        "confirmed_diagnosis": "Community-Acquired Pneumonia (Streptococcus pneumoniae)",
        "clinical_outcome": "Resolved following 7-day course of targeted oral amoxicillin-clavulanate + azithromycin; no ICU admission.",
        "discriminant_features": ["Focal lobar consolidation on CXR", "High procalcitonin distinguishing from viral bronchitis", "Productive purulent sputum"],
        "clinical_takeaway": "Early initiation of empiric antibiotic therapy within 4 hours reduced hospital length of stay by 48 hours.",
    },
    {
        "case_id": "REF-ACS-02",
        "age": 62,
        "sex": "M",
        "symptoms": ["substernal chest pressure", "diaphoresis", "dyspnea", "radiation to left jaw"],
        "history": ["coronary artery disease", "hyperlipidemia", "type 2 diabetes"],
        "labs": [
            {"name": "Troponin-I", "value": 0.42, "unit": "ng/mL", "is_abnormal": True},
            {"name": "CK-MB", "value": 24.0, "unit": "U/L", "is_abnormal": True},
            {"name": "Glucose", "value": 168.0, "unit": "mg/dL", "is_abnormal": True},
        ],
        "confirmed_diagnosis": "Non-ST-Elevation Myocardial Infarction (NSTEMI)",
        "clinical_outcome": "Urgent coronary catheterization identified 90% LAD stenosis; drug-eluting stent placed with uneventful recovery.",
        "discriminant_features": ["Dynamic troponin elevation above 99th percentile", "Exertional retrosternal pressure with diaphoresis", "Absence of fever/cough"],
        "clinical_takeaway": "Serial troponin monitoring at 0h and 3h and prompt cardiology consultation prevented extensive myocardial necrosis.",
    },
    {
        "case_id": "REF-PE-03",
        "age": 39,
        "sex": "F",
        "symptoms": ["sudden dyspnea", "pleuritic chest pain", "tachycardia", "lightheadedness"],
        "history": ["oral contraceptive use", "recent long-haul flight 14h"],
        "labs": [
            {"name": "D-Dimer", "value": 2450.0, "unit": "ng/mL", "is_abnormal": True},
            {"name": "Troponin-I", "value": 0.05, "unit": "ng/mL", "is_abnormal": True},
            {"name": "WBC", "value": 8.2, "unit": "10^3/uL", "is_abnormal": False},
        ],
        "confirmed_diagnosis": "Submassive Acute Pulmonary Embolism (PE)",
        "clinical_outcome": "Treated with therapeutic low-molecular-weight heparin followed by DOAC; outpatient follow-up at 3 months showed resolution.",
        "discriminant_features": ["Acute onset tachypnea with clear lungs on auscultation and normal CXR", "Markedly elevated D-dimer with high Wells score", "Right ventricular strain on echo"],
        "clinical_takeaway": "Sudden pleuritic pain with normal CXR strongly warrants Wells score calculation and CT pulmonary angiography.",
    },
    {
        "case_id": "REF-COPD-04",
        "age": 69,
        "sex": "M",
        "symptoms": ["worsening dyspnea", "increased sputum volume", "wheezing", "low-grade fever"],
        "history": ["severe COPD", "current smoker 50 pack-years", "hypertension"],
        "labs": [
            {"name": "WBC", "value": 12.8, "unit": "10^3/uL", "is_abnormal": True},
            {"name": "pCO2", "value": 52.0, "unit": "mmHg", "is_abnormal": True},
            {"name": "CRP", "value": 45.0, "unit": "mg/L", "is_abnormal": True},
        ],
        "confirmed_diagnosis": "Acute Exacerbation of Chronic Obstructive Pulmonary Disease (AECOPD)",
        "clinical_outcome": "Stabilized with systemic corticosteroids, nebulized bronchodilators, and non-invasive positive pressure ventilation (BiPAP).",
        "discriminant_features": ["Bilateral hyperinflation without focal consolidation", "Baseline chronic cough with acute purulent transition (Anthonisen Type 1)", "Respiratory acidosis on ABG"],
        "clinical_takeaway": "Early non-invasive ventilation avoided endotracheal intubation in severe hypercapnic respiratory failure.",
    },
    {
        "case_id": "REF-HF-05",
        "age": 74,
        "sex": "F",
        "symptoms": ["orthopnea", "paroxysmal nocturnal dyspnea", "bilateral lower extremity edema", "fatigue"],
        "history": ["ischemic cardiomyopathy", "atrial fibrillation", "hypertension"],
        "labs": [
            {"name": "BNP", "value": 1420.0, "unit": "pg/mL", "is_abnormal": True},
            {"name": "Creatinine", "value": 1.6, "unit": "mg/dL", "is_abnormal": True},
            {"name": "Sodium", "value": 134.0, "unit": "mEq/L", "is_abnormal": True},
        ],
        "confirmed_diagnosis": "Acute Decompensated Heart Failure (HFrEF, EF 30%)",
        "clinical_outcome": "Diuresed with IV furosemide infusion; 4.5 kg fluid loss with marked symptom improvement; discharged on guideline-directed medical therapy.",
        "discriminant_features": ["Kerley B lines and cardiomegaly on CXR", "Markedly elevated BNP > 1000 pg/mL", "Bilateral pitting pedal edema and jugular venous distension"],
        "clinical_takeaway": "Distinguishing fluid overload from pulmonary infection via BNP and bedside thoracic ultrasound prevents inappropriate antibiotic delay.",
    },
    {
        "case_id": "REF-AKI-06",
        "age": 65,
        "sex": "M",
        "symptoms": ["decreased urine output", "nausea", "malaise", "flank discomfort"],
        "history": ["hypertension", "osteoarthritis (chronic high-dose NSAID use)"],
        "labs": [
            {"name": "Creatinine", "value": 3.8, "unit": "mg/dL", "is_abnormal": True},
            {"name": "BUN", "value": 58.0, "unit": "mg/dL", "is_abnormal": True},
            {"name": "Potassium", "value": 5.4, "unit": "mEq/L", "is_abnormal": True},
        ],
        "confirmed_diagnosis": "Acute Kidney Injury (KDIGO Stage 3, NSAID-induced Acute Tubular Necrosis)",
        "clinical_outcome": "NSAID cessation, volume resuscitation with isotonic saline; creatinine recovered to baseline 1.1 mg/dL over 10 days.",
        "discriminant_features": ["Rapid threefold increase in serum creatinine within 72 hours", "Recent initiation of OTC naproxen for joint pain", "Absence of hydronephrosis on renal ultrasound"],
        "clinical_takeaway": "Drug-induced nephrotoxicity accounts for up to 20% of community-acquired AKI; immediate medication review is critical.",
    },
]


def _normalize_tokens(tokens: list[str]) -> set[str]:
    """Helper to tokenize and clean clinical strings."""
    cleaned = set()
    for t in tokens:
        for word in t.lower().replace(",", " ").replace(";", " ").split():
            w = word.strip()
            if len(w) > 2 and w not in ("and", "with", "the", "for", "from", "due"):
                cleaned.add(w)
    return cleaned


def _calculate_symptom_similarity(query_symptoms: list[str], ref_symptoms: list[str]) -> tuple[float, list[str]]:
    """Calculates Jaccard overlap between symptoms."""
    q_set = _normalize_tokens(query_symptoms)
    r_set = _normalize_tokens(ref_symptoms)
    if not q_set or not r_set:
        return 0.0, []

    intersection = q_set.intersection(r_set)
    union = q_set.union(r_set)
    jaccard = len(intersection) / len(union) if union else 0.0

    matched: list[str] = []
    for qs in query_symptoms:
        qs_lower = qs.lower()
        if any(rs.lower() in qs_lower or qs_lower in rs.lower() for rs in ref_symptoms):
            matched.append(qs)

    return jaccard, matched


def _calculate_lab_similarity(query_labs: list[dict[str, Any]], ref_labs: list[dict[str, Any]]) -> float:
    """Calculates overlap in abnormal lab indicators."""
    q_abnormal = {l.get("name", "").lower() for l in query_labs if l.get("is_abnormal")}
    r_abnormal = {l.get("name", "").lower() for l in ref_labs if l.get("is_abnormal")}

    if not q_abnormal and not r_abnormal:
        return 0.5  # Neutral when neither has abnormal labs
    if not q_abnormal or not r_abnormal:
        return 0.2

    overlap = q_abnormal.intersection(r_abnormal)
    union = q_abnormal.union(r_abnormal)
    return len(overlap) / len(union) if union else 0.0


def _calculate_demographic_similarity(q_age: Optional[int], q_sex: str, r_age: int, r_sex: str) -> float:
    """Computes age distance score + sex match."""
    score = 0.5
    if q_age is not None:
        diff = abs(q_age - r_age)
        age_score = max(0.0, 1.0 - (diff / 40.0))
        score += age_score * 0.3

    if q_sex and r_sex:
        if q_sex.upper() == r_sex.upper():
            score += 0.2
        elif q_sex.upper() in ("UNKNOWN", "OTHER"):
            score += 0.1

    return min(1.0, score)


def get_reference_cohort() -> list[ReferenceCase]:
    """Loads reference patient cohort from JSON file if available or defaults."""
    settings = get_settings()
    custom_path = settings.demo_data_dir / "reference_cohort.json"

    raw_list: list[dict[str, Any]] = DEFAULT_COHORT
    if custom_path.exists():
        try:
            with open(custom_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list) and len(loaded) > 0:
                    raw_list = loaded
        except Exception as e:
            log.warning("failed_loading_custom_reference_cohort", error=str(e))

    cohort: list[ReferenceCase] = []
    for item in raw_list:
        try:
            cohort.append(ReferenceCase(**item))
        except Exception:
            pass
    return cohort


def find_similar_patients(patient_case: dict[str, Any], top_k: int = 3) -> SimilarPatientResponse:
    """
    Ranks the reference patient cohort according to clinical similarity with the query patient.
    """
    cohort = get_reference_cohort()
    q_symptoms = patient_case.get("symptoms", [])
    if isinstance(q_symptoms, str):
        q_symptoms = [s.strip() for s in q_symptoms.split(",") if s.strip()]

    q_patient = patient_case.get("patient", {})
    q_age = q_patient.get("age") or patient_case.get("age")
    q_sex = q_patient.get("sex") or patient_case.get("sex") or "Unknown"
    q_labs = patient_case.get("labs", [])

    scored_matches: list[SimilarPatientMatch] = []

    for ref in cohort:
        symptom_score, matched_syms = _calculate_symptom_similarity(q_symptoms, ref.symptoms)
        lab_score = _calculate_lab_similarity(q_labs, ref.labs)
        demographic_score = _calculate_demographic_similarity(q_age, str(q_sex), ref.age, ref.sex)

        # Composite weighted score: 50% Symptoms, 30% Labs, 20% Demographics
        composite = (symptom_score * 0.50) + (lab_score * 0.30) + (demographic_score * 0.20)
        # Normalize to 0.0 - 1.0
        composite = round(min(1.0, max(0.05, composite)), 3)

        scored_matches.append(
            SimilarPatientMatch(
                case_id=ref.case_id,
                age=ref.age,
                sex=ref.sex,
                similarity_score=composite,
                symptom_similarity=round(symptom_score, 3),
                lab_similarity=round(lab_score, 3),
                demographic_similarity=round(demographic_score, 3),
                confirmed_diagnosis=ref.confirmed_diagnosis,
                clinical_outcome=ref.clinical_outcome,
                matched_symptoms=matched_syms,
                key_discriminant_pearls=ref.discriminant_features,
                clinical_takeaway=ref.clinical_takeaway,
            )
        )

    # Sort descending by composite similarity score
    scored_matches.sort(key=lambda m: m.similarity_score, reverse=True)
    top_matches = scored_matches[:top_k]

    summary = (
        f"Retrieved {len(top_matches)} benchmark reference encounters from cohort of {len(cohort)}. "
        f"Top matched profile: {top_matches[0].confirmed_diagnosis} "
        f"({int(top_matches[0].similarity_score * 100)}% clinical alignment)."
        if top_matches
        else "No sufficiently matching reference patient encounters found."
    )

    return SimilarPatientResponse(
        query_case_id=patient_case.get("case_id", ""),
        matches=top_matches,
        cohort_size=len(cohort),
        clinical_summary=summary,
    )
