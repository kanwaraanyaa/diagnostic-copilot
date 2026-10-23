import {
  AgenticAnalysisResponse,
  Citation,
  HealthResponse,
  PatientCase,
  VisionAnalysisResponse,
} from '../types/clinical';

const DEFAULT_API_BASE = ''; // Relative to Vite dev server proxy or same origin

export class ClinicalApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = localStorage.getItem('cliniq_backend_url') || DEFAULT_API_BASE;
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  public setBaseUrl(url: string): void {
    this.baseUrl = url.trim().replace(/\/+$/, '');
    localStorage.setItem('cliniq_backend_url', this.baseUrl);
  }

  private getEndpoint(path: string): string {
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return this.baseUrl ? `${this.baseUrl}${cleanPath}` : cleanPath;
  }

  public async getHealth(): Promise<HealthResponse> {
    const res = await fetch(this.getEndpoint('/api/health'), {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Health check failed: HTTP ${res.status}`);
    }
    return res.json();
  }

  public async listCases(limit = 30): Promise<any[]> {
    const res = await fetch(this.getEndpoint(`/api/cases?limit=${limit}`), {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Failed to list cases: HTTP ${res.status}`);
    }
    return res.json();
  }

  public async getCase(caseId: string): Promise<any> {
    const res = await fetch(this.getEndpoint(`/api/cases/${encodeURIComponent(caseId)}`), {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Case not found: HTTP ${res.status}`);
    }
    return res.json();
  }

  public async createCase(caseData: Partial<PatientCase>): Promise<{ success: boolean; case_id: string; warnings: string[] }> {
    const payload = {
      patient_id: caseData.patient_id || '',
      age: caseData.age ?? null,
      sex: caseData.sex || 'Unknown',
      symptoms: Array.isArray(caseData.symptoms) ? caseData.symptoms.join(', ') : caseData.symptoms || '',
      history: Array.isArray(caseData.history) ? caseData.history.join(', ') : caseData.history || '',
      clinical_notes: caseData.clinical_notes || '',
      case_description: caseData.case_description || '',
      labs: caseData.labs || [],
      image_path: caseData.image_path || null,
    };

    const res = await fetch(this.getEndpoint('/api/cases'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
      throw new Error(err.detail || `Failed to create case: HTTP ${res.status}`);
    }
    return res.json();
  }

  public async analyzeAgentic(caseData: Partial<PatientCase>): Promise<AgenticAnalysisResponse> {
    const payload = {
      patient_id: caseData.patient_id || '',
      age: caseData.age ?? null,
      sex: caseData.sex || 'Unknown',
      symptoms: Array.isArray(caseData.symptoms) ? caseData.symptoms.join(', ') : caseData.symptoms || '',
      history: Array.isArray(caseData.history) ? caseData.history.join(', ') : caseData.history || '',
      clinical_notes: caseData.clinical_notes || '',
      case_description: caseData.case_description || '',
      labs: caseData.labs || [],
      image_path: caseData.image_path || null,
    };

    const res = await fetch(this.getEndpoint('/api/analyze/agentic'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
      throw new Error(err.error || `Agentic analysis failed: HTTP ${res.status}`);
    }
    return res.json();
  }

  public async analyzeBaseline(caseData: Partial<PatientCase>): Promise<any> {
    const payload = {
      patient_id: caseData.patient_id || '',
      age: caseData.age ?? null,
      sex: caseData.sex || 'Unknown',
      symptoms: Array.isArray(caseData.symptoms) ? caseData.symptoms.join(', ') : caseData.symptoms || '',
      history: Array.isArray(caseData.history) ? caseData.history.join(', ') : caseData.history || '',
      clinical_notes: caseData.clinical_notes || '',
      case_description: caseData.case_description || '',
      labs: caseData.labs || [],
      image_path: caseData.image_path || null,
    };

    const res = await fetch(this.getEndpoint('/api/analyze'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
      throw new Error(err.error || `Baseline analysis failed: HTTP ${res.status}`);
    }
    return res.json();
  }

  public async retrieveEvidence(query: string, topK = 5): Promise<Citation[]> {
    const res = await fetch(this.getEndpoint('/api/retrieve'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: topK }),
    });

    if (!res.ok) {
      throw new Error(`Evidence retrieval failed: HTTP ${res.status}`);
    }
    const data = await res.json();
    return data.results || [];
  }

  public async uploadImage(file: File): Promise<{ success: boolean; image_path: string; filename: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(this.getEndpoint('/api/upload/image'), {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      throw new Error(`Image upload failed: HTTP ${res.status}`);
    }
    return res.json();
  }

  public async analyzeImage(file: File): Promise<VisionAnalysisResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(this.getEndpoint('/api/analyze/image'), {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      throw new Error(`Vision analysis failed: HTTP ${res.status}`);
    }
    return res.json();
  }

  // --- Phase 3 Advanced Agentic RAG & Evaluation Endpoints ---

  public async getQueryPlan(caseData: Partial<PatientCase>, maxHops = 3): Promise<any> {
    const res = await fetch(this.getEndpoint(`/api/phase3/query-plan?max_hops=${maxHops}`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(caseData),
    });
    if (!res.ok) throw new Error(`Query planning failed: HTTP ${res.status}`);
    return res.json();
  }

  public async getSimilarPatients(caseData: Partial<PatientCase>, topK = 3): Promise<any> {
    const res = await fetch(this.getEndpoint(`/api/phase3/similar-patients?top_k=${topK}`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(caseData),
    });
    if (!res.ok) throw new Error(`Similar patients retrieval failed: HTTP ${res.status}`);
    return res.json();
  }

  public async getEvidenceGraph(caseData: Partial<PatientCase>): Promise<any> {
    const res = await fetch(this.getEndpoint('/api/phase3/evidence-graph'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(caseData),
    });
    if (!res.ok) throw new Error(`Evidence graph failed: HTTP ${res.status}`);
    return res.json();
  }

  public async auditHallucinations(payload: any): Promise<any> {
    const res = await fetch(this.getEndpoint('/api/phase3/hallucination-audit'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Hallucination audit failed: HTTP ${res.status}`);
    return res.json();
  }

  public async getCalibration(payload: any): Promise<any> {
    const res = await fetch(this.getEndpoint('/api/phase3/calibration'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Calibration failed: HTTP ${res.status}`);
    return res.json();
  }

  public async getBenchmarkCases(): Promise<any> {
    const res = await fetch(this.getEndpoint('/api/phase3/benchmark/cases'), {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) throw new Error(`Failed to load benchmark cases: HTTP ${res.status}`);
    return res.json();
  }

  public async runBenchmark(maxCases = 10, category?: string): Promise<any> {
    const url = `/api/phase3/benchmark/run?max_cases=${maxCases}` + (category ? `&category=${encodeURIComponent(category)}` : '');
    const res = await fetch(this.getEndpoint(url), {
      method: 'POST',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) throw new Error(`Benchmark run failed: HTTP ${res.status}`);
    return res.json();
  }

  public async getLatestBenchmark(): Promise<any> {
    const res = await fetch(this.getEndpoint('/api/phase3/benchmark/latest'), {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) throw new Error(`Failed to get benchmark results: HTTP ${res.status}`);
    return res.json();
  }

  public async runAblation(maxCases = 5): Promise<any> {
    const res = await fetch(this.getEndpoint(`/api/phase3/ablation/run?max_cases=${maxCases}`), {
      method: 'POST',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) throw new Error(`Ablation run failed: HTTP ${res.status}`);
    return res.json();
  }

  public async getLatestAblation(): Promise<any> {
    const res = await fetch(this.getEndpoint('/api/phase3/ablation/latest'), {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) throw new Error(`Failed to get ablation results: HTTP ${res.status}`);
    return res.json();
  }
}

export const api = new ClinicalApiClient();
