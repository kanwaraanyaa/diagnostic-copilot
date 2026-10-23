import React, { useEffect, useState } from 'react';
import {
  Activity,
  PlusCircle,
  FileText,
  Server,
  Layers,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  AlertCircle,
  Database,
  Eye,
  CheckCircle2,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { HealthResponse } from '../types/clinical';
import { api } from '../api/client';
import { NavTab } from '../components/layout/Sidebar';

interface ClinicalOverviewProps {
  onNavigate: (tab: NavTab) => void;
  onLoadDemo: () => void;
  health: HealthResponse | null;
  healthLoading: boolean;
  hasActiveReport: boolean;
  hasActiveImage: boolean;
  onSelectCase: (caseItem: any) => void;
}

export const ClinicalOverview: React.FC<ClinicalOverviewProps> = ({
  onNavigate,
  onLoadDemo,
  health,
  healthLoading,
  hasActiveReport,
  hasActiveImage,
  onSelectCase,
}) => {
  const [recentCases, setRecentCases] = useState<any[]>([]);
  const [loadingCases, setLoadingCases] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoadingCases(true);
    setLoadError(null);

    api
      .listCases(10)
      .then((data) => {
        if (isMounted) {
          setRecentCases(data || []);
          setLoadingCases(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setLoadError(err.message || 'Unable to retrieve saved cases');
          setLoadingCases(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Welcome Banner */}
      <div className="bg-linear-to-r from-slate-900 via-slate-800 to-teal-950 rounded-2xl p-6 text-white shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6 border border-slate-700/60">
        <div className="space-y-2 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-500/20 text-teal-300 border border-teal-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
            Clinical Decision Support System
          </div>
          <h2 className="text-xl font-bold tracking-tight text-white">
            MedOrchestr AI Workspace
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed">
            Multi-agent diagnostic orchestration grounded in peer-reviewed medical knowledge, hybrid lexical-dense retrieval, and radiographic vision analytics.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3 shrink-0">
          <Button
            variant="primary"
            leftIcon={<PlusCircle className="w-4 h-4" />}
            onClick={() => onNavigate('new-case')}
          >
            New Clinical Analysis
          </Button>
          <Button
            variant="outline"
            className="bg-white/10 text-white border-white/20 hover:bg-white/20"
            leftIcon={<Sparkles className="w-4 h-4 text-teal-300" />}
            onClick={onLoadDemo}
          >
            Load Educational Demo
          </Button>
        </div>
      </div>

      {/* Backend & Subsystem Telemetry */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Telemetry 1: API Status */}
        <Card className="p-4 bg-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Core Backend
            </span>
            <Server className={`w-4 h-4 ${health ? 'text-teal-600' : 'text-rose-500'}`} />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-900">
              {healthLoading ? 'Checking...' : health ? 'Online' : 'Offline'}
            </span>
            {health && (
              <span className="text-xs text-slate-500 font-mono">v{health.version}</span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {health ? 'Clinical Intelligence Service Active' : 'System Service Unavailable'}
          </p>
        </Card>

        {/* Telemetry 2: Multi-Agent Orchestrator */}
        <Card className="p-4 bg-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Agent Orchestration
            </span>
            <Layers className="w-4 h-4 text-teal-600" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-900">6 Agents</span>
            <span className="text-xs text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded font-medium border border-teal-200">
              LangGraph
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            GP, Retrieval, Radiologist, Specialist, Critic & Synthesizer
          </p>
        </Card>

        {/* Telemetry 3: Hybrid RAG Engine */}
        <Card className="p-4 bg-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Knowledge Base
            </span>
            <Database className="w-4 h-4 text-teal-600" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-900">Hybrid Search</span>
            <span className="text-xs text-slate-500 font-mono">Dense + BM25</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            ChromaDB embeddings with lexical cross-matching rerank
          </p>
        </Card>

        {/* Telemetry 4: Medical Vision Subsystem */}
        <Card className="p-4 bg-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Medical Vision
            </span>
            <Eye className="w-4 h-4 text-teal-600" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-900">Radiography</span>
            <span className="text-xs text-slate-500 font-mono">CXR / PNG</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Sanitization, resizing, and calibrated anatomical assessment
          </p>
        </Card>
      </div>

      {/* Main Content Grid: Saved Cases & Fast Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Recent Patient Cases */}
        <div className="lg:col-span-2 space-y-4">
          <Card
            title={
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-teal-700" />
                <span>Recent Clinical Cases in Database</span>
              </div>
            }
            subtitle="Verified SQLite persistence records"
            action={
              <Button
                variant="ghost"
                size="sm"
                rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                onClick={() => onNavigate('cases')}
              >
                View All Cases
              </Button>
            }
            bodyClassName="p-0"
          >
            {loadingCases ? (
              <div className="p-8 text-center text-sm text-slate-500">
                Loading clinical cases from database...
              </div>
            ) : loadError ? (
              <div className="p-6 text-center text-sm text-rose-600 bg-rose-50/50 flex flex-col items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                <span>{loadError}</span>
              </div>
            ) : recentCases.length === 0 ? (
              <div className="p-10 text-center space-y-3">
                <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
                  <FileText className="w-5 h-5" />
                </div>
                <h4 className="text-sm font-semibold text-slate-700">No Patient Cases Recorded</h4>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  Begin by starting a new clinical analysis or loading the preconfigured educational demo case.
                </p>
                <div className="flex justify-center gap-3 pt-2">
                  <Button size="sm" onClick={() => onNavigate('new-case')}>
                    Create First Case
                  </Button>
                  <Button size="sm" variant="outline" onClick={onLoadDemo}>
                    Load Synthetic Demo
                  </Button>
                </div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Case Identifier</th>
                      <th className="px-4 py-3 font-semibold">Demographics</th>
                      <th className="px-4 py-3 font-semibold">Primary Symptoms</th>
                      <th className="px-4 py-3 font-semibold">Labs Recorded</th>
                      <th className="px-4 py-3 font-semibold text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {recentCases.map((c) => (
                      <tr key={c.case_id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-4 py-3 font-mono font-medium text-slate-900">
                          {c.case_id}
                        </td>
                        <td className="px-4 py-3 text-slate-600">
                          {c.age ? `${c.age}y` : 'Age N/A'}, {c.sex || 'Unknown'}
                        </td>
                        <td className="px-4 py-3 text-slate-700 max-w-xs truncate">
                          {Array.isArray(c.symptoms) ? c.symptoms.join(', ') : c.symptoms || '—'}
                        </td>
                        <td className="px-4 py-3">
                          <span className="font-medium text-slate-700">
                            {Array.isArray(c.labs) ? `${c.labs.length} tests` : '0 tests'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              onSelectCase(c);
                              onNavigate('new-case');
                            }}
                          >
                            Load Case
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {/* Quick Analysis Navigation Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div
              onClick={() => onNavigate('imaging')}
              className="p-4 bg-white rounded-xl border border-slate-200 hover:border-teal-400 hover:shadow-xs transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 rounded-lg bg-teal-50 text-teal-700 group-hover:bg-teal-600 group-hover:text-white transition-colors">
                  <Eye className="w-4 h-4" />
                </div>
                <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-teal-600 transition-colors" />
              </div>
              <h4 className="text-sm font-semibold text-slate-800">Radiology Workstation</h4>
              <p className="text-xs text-slate-500 mt-1">
                Upload or inspect chest radiography with localized findings and technical quality assessment.
              </p>
            </div>

            <div
              onClick={() => onNavigate('evidence')}
              className="p-4 bg-white rounded-xl border border-slate-200 hover:border-teal-400 hover:shadow-xs transition-all cursor-pointer group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="p-2 rounded-lg bg-teal-50 text-teal-700 group-hover:bg-teal-600 group-hover:text-white transition-colors">
                  <Database className="w-4 h-4" />
                </div>
                <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-teal-600 transition-colors" />
              </div>
              <h4 className="text-sm font-semibold text-slate-800">Evidence Explorer</h4>
              <p className="text-xs text-slate-500 mt-1">
                Directly query the peer-reviewed clinical knowledge base using hybrid dense-sparse RAG.
              </p>
            </div>
          </div>
        </div>

        {/* Right Column: Active Session & Safety Guidelines */}
        <div className="space-y-4">
          <Card
            title="Active Session Overview"
            subtitle="Current in-memory workspace"
          >
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Analysis Status:</span>
                <Badge variant={hasActiveReport ? 'success' : 'neutral'}>
                  {hasActiveReport ? 'Report Available' : 'Idle / Not Run'}
                </Badge>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Medical Imaging:</span>
                <span className="font-medium text-slate-700">
                  {hasActiveImage ? 'Radiograph Attached' : 'None Attached'}
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <span className="text-slate-500">Decision Support Mode:</span>
                <span className="font-medium text-teal-800">Multi-Agent Clinical Consensus</span>
              </div>

              {hasActiveReport && (
                <div className="pt-2">
                  <Button
                    className="w-full"
                    size="sm"
                    variant="primary"
                    rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                    onClick={() => onNavigate('reports')}
                  >
                    Open Active CDS Report
                  </Button>
                </div>
              )}
            </div>
          </Card>

          <Card
            title={
              <div className="flex items-center gap-1.5 text-slate-800">
                <ShieldAlert className="w-4 h-4 text-amber-600" />
                <span>Clinical Decision Support Notice</span>
              </div>
            }
          >
            <div className="text-xs text-slate-600 space-y-2 leading-relaxed">
              <p>
                <strong>For research and educational use only.</strong> This software provides synthesized diagnostic hypotheses and evidence citations for clinician review.
              </p>
              <ul className="list-disc pl-4 space-y-1 text-slate-500 text-[11px]">
                <li>Does not provide definitive diagnoses.</li>
                <li>Does not prescribe medications or dosages.</li>
                <li>All visual and textual findings require qualified physician verification.</li>
              </ul>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
