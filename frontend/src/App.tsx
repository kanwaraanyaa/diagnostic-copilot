import React, { useState, useEffect } from 'react';
import { Sidebar, NavTab } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { ClinicalOverview } from './views/ClinicalOverview';
import { PatientWorkspace } from './views/PatientWorkspace';
import { ImagingWorkspace } from './views/ImagingWorkspace';
import { AgentWorkflow } from './views/AgentWorkflow';
import { EvidenceExplorer } from './views/EvidenceExplorer';
import { ClinicalReport } from './views/ClinicalReport';
import { CasesList } from './views/CasesList';
import { SettingsView } from './views/SettingsView';
import { ResearchEvaluation } from './views/ResearchEvaluation';
import { DEMO_CASE } from './data/demoCase';
import {
  AgenticAnalysisResponse,
  Citation,
  FinalReport,
  HealthResponse,
  PatientCase,
} from './types/clinical';
import { api } from './api/client';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';

export const App: React.FC = () => {
  // Navigation State
  const [activeTab, setActiveTab] = useState<NavTab>('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);

  // System Health
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(true);

  // Active Patient State
  const [currentCase, setCurrentCase] = useState<Partial<PatientCase>>({
    patient_id: '',
    age: null,
    sex: 'Unknown',
    symptoms: [],
    history: [],
    medications: [],
    allergies: [],
    vitals: {},
    labs: [],
    clinical_notes: '',
    image_path: null,
  });
  const [isDemoLoaded, setIsDemoLoaded] = useState<boolean>(false);

  // Analysis Results State
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [agenticResponse, setAgenticResponse] = useState<AgenticAnalysisResponse | null>(null);
  const [finalReport, setFinalReport] = useState<FinalReport | null>(null);
  const [activeCitations, setActiveCitations] = useState<Citation[]>([]);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [notification, setNotification] = useState<string | null>(null);

  // Check health on mount
  const checkHealth = () => {
    setHealthLoading(true);
    api
      .getHealth()
      .then((data) => {
        setHealth(data);
        setHealthLoading(false);
      })
      .catch(() => {
        setHealth(null);
        setHealthLoading(false);
      });
  };

  useEffect(() => {
    checkHealth();
  }, []);

  // Action: Load Synthetic Demo Case & CXR
  const handleLoadDemo = () => {
    setCurrentCase(DEMO_CASE);
    setIsDemoLoaded(true);
    setNotification('Synthetic educational clinical case & CXR loaded.');
    setTimeout(() => setNotification(null), 4000);
  };

  // Action: Reset Session
  const handleResetSession = () => {
    setCurrentCase({
      patient_id: '',
      age: null,
      sex: 'Unknown',
      symptoms: [],
      history: [],
      medications: [],
      allergies: [],
      vitals: {},
      labs: [],
      clinical_notes: '',
      image_path: null,
    });
    setIsDemoLoaded(false);
    setAgenticResponse(null);
    setFinalReport(null);
    setActiveCitations([]);
    setGlobalError(null);
    setNotification('Clinical workspace session reset.');
    setTimeout(() => setNotification(null), 3000);
  };

  // Action: Load Saved Case from Database
  const handleSelectSavedCase = (caseRecord: any) => {
    setCurrentCase({
      case_id: caseRecord.case_id,
      patient_id: caseRecord.case_id,
      age: caseRecord.age,
      sex: caseRecord.sex,
      symptoms: Array.isArray(caseRecord.symptoms) ? caseRecord.symptoms : [],
      history: Array.isArray(caseRecord.history) ? caseRecord.history : [],
      labs: Array.isArray(caseRecord.labs) ? caseRecord.labs : [],
      clinical_notes: caseRecord.clinical_notes || '',
      case_description: caseRecord.case_description || '',
      image_path: null,
    });
    setIsDemoLoaded(false);
    setNotification(`Loaded saved case ${caseRecord.case_id} into workspace.`);
    setTimeout(() => setNotification(null), 3500);
  };

  // Action: Run Analysis (Agentic Multi-Agent or Baseline RAG)
  const handleRunAnalysis = async (mode: 'agentic' | 'baseline') => {
    setIsAnalyzing(true);
    setGlobalError(null);

    try {
      if (mode === 'agentic') {
        const res = await api.analyzeAgentic(currentCase);
        if (res.success && res.final_report) {
          setAgenticResponse(res);
          setFinalReport(res.final_report);
          setActiveCitations(res.final_report.evidence_citations || []);
          setNotification('Multi-agent clinical debate completed. Synthesized report ready.');
          setActiveTab('reports');
        } else {
          throw new Error(res.error || 'Agentic multi-agent workflow encountered an error');
        }
      } else {
        const res = await api.analyzeBaseline(currentCase);
        if (res.success && res.report) {
          const transformed: FinalReport = {
            case_id: res.report.case_id,
            patient_summary: res.report.patient_summary,
            key_clinical_findings: res.report.important_findings || [],
            differential_considerations: res.report.differential_considerations || [],
            evidence_citations: res.report.citations || [],
            suggested_next_questions: res.report.suggested_questions || [],
            safety_disclaimer: res.report.disclaimer,
          };
          setFinalReport(transformed);
          setActiveCitations(transformed.evidence_citations);
          setNotification('Baseline RAG analysis completed. Report ready.');
          setActiveTab('reports');
        } else {
          throw new Error(res.error || 'Baseline RAG analysis failed');
        }
      }
    } catch (err: any) {
      setGlobalError(err.message || 'Analysis failed. Please verify the backend connection.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Header Titles Mapping
  const tabTitles: Record<NavTab, { title: string; subtitle: string }> = {
    overview: {
      title: 'Clinical Overview Dashboard',
      subtitle: 'System telemetry, verified SQLite cases, and quick clinical actions',
    },
    cases: {
      title: 'Patient Cases Directory',
      subtitle: 'Historical case records and structured diagnostic profiles',
    },
    'new-case': {
      title: 'Clinical Case Analysis Workspace',
      subtitle: '10-section structured case intake, dynamic lab testing, and analysis trigger',
    },
    imaging: {
      title: 'Radiology Workstation',
      subtitle: 'Chest radiograph upload, technical quality verification, and localized findings',
    },
    workflow: {
      title: 'AI Multi-Agent Execution Trace',
      subtitle: 'Visual LangGraph node state, debate iterations, and structured agent logs',
    },
    evidence: {
      title: 'Evidence Explorer & Knowledge Base',
      subtitle: 'Ground-truth medical literature citations and interactive hybrid RAG search',
    },
    reports: {
      title: 'Clinical Decision Support Report',
      subtitle: 'Formal 9-section report formatted for medical review and print export',
    },
    evaluation: {
      title: 'Research, Benchmarking & Evaluation Suite',
      subtitle: '50-case benchmark evaluation, ablation matrices, and evidence knowledge graphs',
    },
    settings: {
      title: 'System Settings & Architecture',
      subtitle: 'API endpoints, service status, and regulatory disclaimers',
    },
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900 font-sans">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        health={health}
        healthLoading={healthLoading}
        hasActiveReport={Boolean(finalReport)}
        hasActiveImage={Boolean(currentCase.image_path)}
      />

      {/* Main Workspace Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Top Header */}
        <Header
          title={tabTitles[activeTab].title}
          subtitle={tabTitles[activeTab].subtitle}
          currentCase={currentCase}
          onLoadDemo={handleLoadDemo}
          onReset={handleResetSession}
          isDemoLoaded={isDemoLoaded}
          onNavigateToReport={() => setActiveTab('reports')}
          hasActiveReport={Boolean(finalReport)}
        />

        {/* Global Notification Banner */}
        {notification && (
          <div className="no-print bg-teal-50 border-b border-teal-200 px-6 py-2.5 text-xs text-teal-900 flex items-center justify-between animate-fadeIn">
            <span className="flex items-center gap-2 font-medium">
              <CheckCircle2 className="w-4 h-4 text-teal-600" />
              {notification}
            </span>
            <button
              onClick={() => setNotification(null)}
              className="text-teal-700 hover:text-teal-900 font-bold"
            >
              ×
            </button>
          </div>
        )}

        {/* Global Error Banner */}
        {globalError && (
          <div className="no-print bg-rose-50 border-b border-rose-200 px-6 py-2.5 text-xs text-rose-900 flex items-center justify-between">
            <span className="flex items-center gap-2 font-medium">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              {globalError}
            </span>
            <button
              onClick={() => setGlobalError(null)}
              className="text-rose-700 hover:text-rose-900 font-bold"
            >
              ×
            </button>
          </div>
        )}

        {/* Dynamic Workspace Body */}
        <main className="flex-1 overflow-y-auto">
          {activeTab === 'overview' && (
            <ClinicalOverview
              onNavigate={setActiveTab}
              onLoadDemo={handleLoadDemo}
              health={health}
              healthLoading={healthLoading}
              hasActiveReport={Boolean(finalReport)}
              hasActiveImage={Boolean(currentCase.image_path)}
              onSelectCase={handleSelectSavedCase}
            />
          )}

          {activeTab === 'cases' && (
            <CasesList
              onSelectCase={handleSelectSavedCase}
              onNavigate={setActiveTab}
            />
          )}

          {activeTab === 'new-case' && (
            <PatientWorkspace
              currentCase={currentCase}
              onChangeCase={setCurrentCase}
              onRunAnalysis={handleRunAnalysis}
              isAnalyzing={isAnalyzing}
              onNavigateToImaging={() => setActiveTab('imaging')}
              isDemoLoaded={isDemoLoaded}
            />
          )}

          {activeTab === 'imaging' && (
            <ImagingWorkspace
              activeImagePath={currentCase.image_path || null}
              onSelectImage={(path) => setCurrentCase((c) => ({ ...c, image_path: path }))}
              onAttachToPatient={(path) => setCurrentCase((c) => ({ ...c, image_path: path }))}
            />
          )}

          {activeTab === 'workflow' && (
            <AgentWorkflow
              analysisResponse={agenticResponse}
              onNavigate={setActiveTab}
              isAnalyzing={isAnalyzing}
            />
          )}

          {activeTab === 'evidence' && (
            <EvidenceExplorer activeCitations={activeCitations} />
          )}

          {activeTab === 'reports' && (
            <ClinicalReport
              report={finalReport}
              patientCase={currentCase}
              onNavigate={setActiveTab}
            />
          )}

          {activeTab === 'evaluation' && (
            <ResearchEvaluation
              currentCase={currentCase}
              finalReport={finalReport}
            />
          )}

          {activeTab === 'settings' && (
            <SettingsView
              health={health}
              onRefreshHealth={checkHealth}
              healthLoading={healthLoading}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
