import React, { useState } from 'react';
import {
  Settings,
  Server,
  Database,
  Cpu,
  ShieldAlert,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { HealthResponse } from '../types/clinical';
import { api } from '../api/client';

interface SettingsViewProps {
  health: HealthResponse | null;
  onRefreshHealth: () => void;
  healthLoading: boolean;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  health,
  onRefreshHealth,
  healthLoading,
}) => {
  const [backendUrl, setBackendUrl] = useState<string>(api.getBaseUrl() || 'http://localhost:8000');
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const handleSaveUrl = () => {
    api.setBaseUrl(backendUrl);
    setSaveStatus('Backend URL updated. Re-pinging service health...');
    onRefreshHealth();
    setTimeout(() => setSaveStatus(null), 3000);
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <Settings className="w-5 h-5 text-teal-700" />
          System Settings & Platform Architecture
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Configure API endpoints, inspect backend health telemetry, and review clinical safety parameters.
        </p>
      </div>

      {/* Backend Connection Config */}
      <Card
        title={
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-teal-700" />
            <span>Clinical Intelligence Service Connection</span>
          </div>
        }
        subtitle="Specify the REST API address for the diagnostic intelligence network"
      >
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3 items-end">
            <Input
              label="Service API Base URL"
              value={backendUrl}
              onChange={(e) => setBackendUrl(e.target.value)}
              placeholder="e.g. http://localhost:8000"
              helperText="Set to the endpoint of the diagnostic intelligence service"
              containerClassName="flex-1"
            />
            <Button size="md" variant="primary" onClick={handleSaveUrl}>
              Save & Reconnect
            </Button>
          </div>

          {saveStatus && (
            <p className="text-xs text-emerald-700 flex items-center gap-1.5 font-medium">
              <CheckCircle2 className="w-4 h-4" />
              {saveStatus}
            </p>
          )}

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-500">Service Status:</span>
              <span
                className={`font-semibold inline-flex items-center gap-1.5 ${
                  health ? 'text-emerald-700' : 'text-rose-600'
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    health ? 'bg-emerald-500' : 'bg-rose-500'
                  }`}
                />
                {healthLoading ? 'Testing connection...' : health ? 'Operational' : 'Offline / Unreachable'}
              </span>
            </div>

            <Button
              size="sm"
              variant="outline"
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
              onClick={onRefreshHealth}
              isLoading={healthLoading}
            >
              Ping Server
            </Button>
          </div>
        </div>
      </Card>

      {/* Architectural Telemetry */}
      <Card
        title={
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-teal-700" />
            <span>Subsystem Components & Architecture</span>
          </div>
        }
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
            <span className="font-semibold text-slate-800 block">LangGraph Multi-Agent Engine</span>
            <p className="text-slate-500 text-[11px]">
              Orchestrates 6 specialized nodes (GP, Retrieval, Radiologist, Specialist, Critic, Synthesizer) with max 3 debate cycles.
            </p>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
            <span className="font-semibold text-slate-800 block">Hybrid RAG Knowledge Base</span>
            <p className="text-slate-500 text-[11px]">
              ChromaDB dense vectors (MiniLM-L6) + BM25 sparse index with cross-matching rerank and citation binding.
            </p>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
            <span className="font-semibold text-slate-800 block">Medical Vision Subsystem</span>
            <p className="text-slate-500 text-[11px]">
              Supports Gemini Vision, OpenAI Vision, or local radiographic heuristic adapter with dimension sanity checks.
            </p>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
            <span className="font-semibold text-slate-800 block">Test & Verification Suite</span>
            <p className="text-slate-500 text-[11px]">
              67 unit and integration tests passing across patient normalization, RAG retrieval, agents, vision, and API routes.
            </p>
          </div>
        </div>
      </Card>

      {/* Mandatory Safety Notice */}
      <Card
        title={
          <div className="flex items-center gap-2 text-slate-900">
            <ShieldAlert className="w-4 h-4 text-amber-600" />
            <span>Clinical Disclaimer & Regulatory Boundaries</span>
          </div>
        }
      >
        <div className="text-xs text-slate-600 space-y-3 leading-relaxed">
          <p className="font-semibold text-slate-900">
            "For research and educational use only. This system does not provide a confirmed medical diagnosis and does not replace a qualified healthcare professional."
          </p>
          <ul className="list-disc pl-4 space-y-1 text-slate-500 text-[11px]">
            <li>Prescription of medications and dosages is strictly prohibited.</li>
            <li>No patient identifiable health information (PHI) should be transmitted or logged.</li>
            <li>DICOM transmission is not claimed without certified PACS integration.</li>
            <li>All machine learning outputs must be corroborated with clinical laboratory results and physical examination.</li>
          </ul>
        </div>
      </Card>
    </div>
  );
};
