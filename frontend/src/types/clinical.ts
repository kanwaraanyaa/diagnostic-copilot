export type Sex = 'M' | 'F' | 'Other' | 'Unknown';

export type UncertaintyLevel = 'low' | 'moderate' | 'high' | 'unknown';

export type DocumentType =
  | 'clinical_guideline'
  | 'peer_reviewed'
  | 'medical_database'
  | 'educational'
  | 'case_report'
  | 'unknown';

export interface LabResult {
  name: string;
  value: number;
  unit: string;
  reference_range: string;
  is_abnormal?: boolean;
}

export interface VitalSigns {
  heartRate?: number;
  bloodPressureSys?: number;
  bloodPressureDia?: number;
  respiratoryRate?: number;
  oxygenSaturation?: number;
  temperature?: number;
}

export interface Medication {
  name: string;
  dosage: string;
  frequency: string;
}

export interface PatientCase {
  case_id: string;
  patient_id?: string;
  age?: number | null;
  sex: Sex;
  symptoms: string[];
  history: string[];
  medications?: Medication[];
  allergies?: string[];
  vitals?: VitalSigns;
  labs: LabResult[];
  clinical_notes: string;
  case_description?: string;
  image_path?: string | null;
  created_at?: string;
}

export interface Citation {
  source_id: string;
  title: string;
  source: string;
  document_type: DocumentType;
  content: string;
  relevance_score: number;
  chunk_id?: string;
  section?: string;
}

export interface DifferentialCondition {
  condition: string;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  uncertainty: UncertaintyLevel;
  source_ids: string[];
}

export interface DiagnosticReport {
  case_id: string;
  patient_summary: string;
  important_findings: string[];
  differential_considerations: DifferentialCondition[];
  suggested_questions: string[];
  citations: Citation[];
  disclaimer: string;
  generated_at: string;
  errors?: string[];
}

export interface ImageFinding {
  location: string;
  finding: string;
  confidence: UncertaintyLevel;
  source?: string;
}

export interface ImagingFindingsSection {
  modality: string;
  technical_quality: string;
  model_used: string;
  overall_impression: string;
  findings: ImageFinding[];
}

export interface AgentAssessmentGPA {
  patient_summary?: string;
  initial_hypotheses?: Array<{
    condition: string;
    clinical_rationale: string;
  }>;
  risk_indicators?: string[];
}

export interface AgentAssessmentSpecialist {
  specialist_assessment?: string;
  differential_considerations?: Array<{
    condition: string;
    uncertainty: UncertaintyLevel;
    supporting_evidence: string[];
    contradicting_evidence: string[];
    source_ids: string[];
  }>;
  diagnostic_recommendations?: string[];
}

export interface AgentAssessmentRadiologist {
  overall_impression?: string;
  modality?: string;
  technical_quality?: string;
  findings?: ImageFinding[];
}

export interface AgentAssessments {
  general_physician?: AgentAssessmentGPA;
  specialist?: AgentAssessmentSpecialist;
  radiologist?: AgentAssessmentRadiologist;
}

export interface CriticFindings {
  summary: string;
  supported_claims: string[];
  unsupported_claims: string[];
  missing_information: string[];
  revision_required?: boolean;
}

export interface FinalReport {
  case_id?: string;
  patient_summary: string;
  key_clinical_findings: string[];
  imaging_findings?: ImagingFindingsSection;
  agent_assessments?: AgentAssessments;
  differential_considerations: DifferentialCondition[];
  evidence_citations: Citation[];
  critic_findings?: CriticFindings;
  suggested_next_questions: string[];
  safety_disclaimer: string;
}

export interface AgentLogItem {
  agent: string;
  action: string;
  timestamp?: string;
  iteration?: number;
  [key: string]: any;
}

export interface AgenticAnalysisResponse {
  success: boolean;
  case_id?: string;
  iteration_count: number;
  final_report?: FinalReport;
  agent_logs?: AgentLogItem[];
  image_findings?: ImageFinding[];
  error?: string;
}

export interface VisionAnalysisResponse {
  success: boolean;
  image_path: string;
  image_modality: string;
  findings: ImageFinding[];
  overall_impression: string;
  technical_quality: string;
  model_used: string;
  error?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  phase: number;
}
