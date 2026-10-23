import React, { useState } from 'react';
import {
  GitBranch,
  Stethoscope,
  Database,
  Eye,
  HeartPulse,
  Scale,
  FileCheck,
  CheckCircle2,
  Clock,
  Layers,
  ArrowRight,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge, UncertaintyBadge } from '../components/ui/Badge';
import { AgenticAnalysisResponse, AgentLogItem } from '../types/clinical';
import { NavTab } from '../components/layout/Sidebar';

interface AgentWorkflowProps {
  analysisResponse: AgenticAnalysisResponse | null;
  onNavigate: (tab: NavTab) => void;
  isAnalyzing: boolean;
}

export const AgentWorkflow: React.FC<AgentWorkflowProps> = ({
  analysisResponse,
  onNavigate,
  isAnalyzing,
}) => {
  const [selectedAgentKey, setSelectedAgentKey] = useState<string>('gp_agent');
  const [expandedLogIndices, setExpandedLogIndices] = useState<Record<number, boolean>>({});

  const toggleLogExpand = (idx: number) => {
    setExpandedLogIndices((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const hasExecuted = Boolean(analysisResponse && analysisResponse.success);
  const rep = analysisResponse?.final_report;
  const logs = analysisResponse?.agent_logs || [];
  const iterationCount = analysisResponse?.iteration_count || 1;

  // 6 Specialized Agent nodes in LangGraph workflow
  const agentNodes = [
    {
      key: 'gp_agent',
      name: 'General Physician Agent',
      shortName: 'GP Triage',
      icon: Stethoscope,
      description: 'Case triage, baseline risk indicators, and initial clinical hypotheses formulation',
      assessment: rep?.agent_assessments?.general_physician,
    },
    {
      key: 'retrieval_agent',
      name: 'Clinical Retrieval Agent',
      shortName: 'Hybrid RAG',
      icon: Database,
      description: 'Targeted lexical + dense search over peer-reviewed medical corpus with citation binding',
      assessment: rep?.evidence_citations,
    },
    {
      key: 'radiology_agent',
      name: 'Radiology Vision Agent',
      shortName: 'Radiologist',
      icon: Eye,
      description: 'Radiographic image analysis, visual feature extraction, and uncertainty calibration',
      assessment: rep?.agent_assessments?.radiologist,
    },
    {
      key: 'specialist_agent',
      name: 'Specialist Agent',
      shortName: 'Specialist',
      icon: HeartPulse,
      description: 'Deep cardiopulmonary differential reasoning, correlation, and evidence weighting',
      assessment: rep?.agent_assessments?.specialist,
    },
    {
      key: 'critic_agent',
      name: 'Critic & Verifier Agent',
      shortName: 'Critic / Audit',
      icon: Scale,
      description: 'Adversarial audit of evidence grounding, contradiction checks, and debate loop trigger',
      assessment: rep?.critic_findings,
    },
    {
      key: 'synthesizer',
      name: 'Final Clinical Synthesizer',
      shortName: 'Synthesizer',
      icon: FileCheck,
      description: 'Structured 9-section Clinical Decision Support report compilation with safety bounds',
      assessment: rep?.differential_considerations,
    },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-teal-700" />
            Multi-Agent LangGraph Workflow Orchestration
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Stateful collaborative multi-agent execution trace with iterative critique and clinical verification.
          </p>
        </div>

        {hasExecuted && (
          <Button
            size="sm"
            variant="primary"
            rightIcon={<ArrowRight className="w-4 h-4" />}
            onClick={() => onNavigate('reports')}
          >
            View Synthesized CDS Report
          </Button>
        )}
      </div>

      {/* Execution Status Banner */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className={`w-3 h-3 rounded-full ${
              isAnalyzing
                ? 'bg-amber-500 animate-ping'
                : hasExecuted
                ? 'bg-emerald-500'
                : 'bg-slate-300'
            }`}
          />
          <div>
            <span className="text-xs font-semibold text-slate-800">
              {isAnalyzing
                ? 'Workflow Execution In Progress...'
                : hasExecuted
                ? 'Workflow Execution Completed'
                : 'Workflow Ready (No Active Run)'}
            </span>
            <p className="text-[11px] text-slate-500">
              {hasExecuted
                ? `Completed via LangGraph with ${iterationCount} debate iteration cycle(s)`
                : 'Configure a patient case in the Patient Workspace to run analysis.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
            <span className="text-slate-400">Iterations: </span>
            <span className="font-bold text-slate-800">{iterationCount} / 3 max</span>
          </div>
          <div className="bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
            <span className="text-slate-400">Agent Events: </span>
            <span className="font-bold text-slate-800">{logs.length} logged</span>
          </div>
          <div className="bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
            <span className="text-slate-400">Imaging: </span>
            <span className="font-bold text-teal-700">
              {analysisResponse?.image_findings?.length ? 'Analyzed' : 'Fallback / None'}
            </span>
          </div>
        </div>
      </div>

      {/* Agent Topology Flow (6 Nodes) */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {agentNodes.map((agent, i) => {
          const Icon = agent.icon;
          const isSelected = selectedAgentKey === agent.key;

          return (
            <div
              key={agent.key}
              onClick={() => setSelectedAgentKey(agent.key)}
              className={`p-3.5 rounded-xl border transition-all cursor-pointer flex flex-col justify-between select-none ${
                isSelected
                  ? 'border-teal-600 bg-teal-50/60 ring-2 ring-teal-500/30 shadow-xs'
                  : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center ${
                      isSelected
                        ? 'bg-teal-700 text-white'
                        : hasExecuted
                        ? 'bg-slate-100 text-slate-700'
                        : 'bg-slate-100 text-slate-400'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-mono text-slate-400">0{i + 1}</span>
                </div>
                <h4 className="text-xs font-bold text-slate-900 leading-tight">
                  {agent.shortName}
                </h4>
                <p className="text-[10px] text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                  {agent.description}
                </p>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between">
                <span
                  className={`text-[10px] font-semibold flex items-center gap-1 ${
                    hasExecuted ? 'text-emerald-700' : 'text-slate-400'
                  }`}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      hasExecuted ? 'bg-emerald-500' : 'bg-slate-300'
                    }`}
                  />
                  {hasExecuted ? 'Completed' : 'Pending'}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Agent Assessment Inspector */}
      {hasExecuted && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Agent Assessment Detail (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            <Card
              title={
                <div className="flex items-center gap-2">
                  <span>Structured Output:</span>
                  <span className="text-teal-800 font-semibold">
                    {agentNodes.find((a) => a.key === selectedAgentKey)?.name}
                  </span>
                </div>
              }
              subtitle="Verified state object output from LangGraph"
            >
              {/* GP Agent Output */}
              {selectedAgentKey === 'gp_agent' && (
                <div className="space-y-4 text-xs">
                  <div>
                    <h5 className="font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Case Triage Summary:
                    </h5>
                    <p className="text-slate-800 bg-slate-50 p-3 rounded-lg border border-slate-200 leading-relaxed">
                      {rep?.agent_assessments?.general_physician?.patient_summary ||
                        'GP patient summary compiled.'}
                    </p>
                  </div>

                  {rep?.agent_assessments?.general_physician?.initial_hypotheses && (
                    <div>
                      <h5 className="font-semibold text-slate-700 uppercase tracking-wider mb-2">
                        Initial Hypotheses:
                      </h5>
                      <div className="space-y-2">
                        {rep.agent_assessments.general_physician.initial_hypotheses.map((h, idx) => (
                          <div
                            key={idx}
                            className="p-3 bg-white border border-slate-200 rounded-lg space-y-1"
                          >
                            <span className="font-bold text-slate-900">{h.condition}</span>
                            <p className="text-slate-600 text-[11px] leading-relaxed">
                              {h.clinical_rationale}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Retrieval Agent Output */}
              {selectedAgentKey === 'retrieval_agent' && (
                <div className="space-y-3 text-xs">
                  <p className="text-slate-600">
                    Retrieved {rep?.evidence_citations?.length || 0} peer-reviewed clinical knowledge chunks using dense vector embeddings and BM25 sparse matching.
                  </p>
                  <div className="space-y-2">
                    {rep?.evidence_citations?.map((cit, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-1"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-teal-900">
                            [{cit.source_id}] {cit.title}
                          </span>
                          <span className="font-mono text-[11px] text-slate-500">
                            Relevance: {(cit.relevance_score || 0).toFixed(2)}
                          </span>
                        </div>
                        <p className="text-slate-700 text-[11px] line-clamp-3">{cit.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Radiology Agent Output */}
              {selectedAgentKey === 'radiology_agent' && (
                <div className="space-y-4 text-xs">
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-slate-500 block mb-1">Radiology Impression:</span>
                    <p className="font-medium text-slate-800">
                      {rep?.agent_assessments?.radiologist?.overall_impression ||
                        rep?.imaging_findings?.overall_impression ||
                        'Radiology assessed with calibrated uncertainty.'}
                    </p>
                  </div>

                  {rep?.imaging_findings?.findings && (
                    <div>
                      <h5 className="font-semibold text-slate-700 uppercase tracking-wider mb-2">
                        Localized Radiographic Findings:
                      </h5>
                      <div className="space-y-2">
                        {rep.imaging_findings.findings.map((f, i) => (
                          <div
                            key={i}
                            className="p-2.5 bg-white border border-slate-200 rounded-lg flex items-center justify-between"
                          >
                            <div>
                              <span className="font-semibold text-slate-900">{f.location}</span>
                              <p className="text-slate-600 text-[11px]">{f.finding}</p>
                            </div>
                            <UncertaintyBadge level={f.confidence} />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Specialist Agent Output */}
              {selectedAgentKey === 'specialist_agent' && (
                <div className="space-y-4 text-xs">
                  <div>
                    <h5 className="font-semibold text-slate-700 uppercase tracking-wider mb-1">
                      Cardiopulmonary Assessment:
                    </h5>
                    <p className="text-slate-800 bg-slate-50 p-3 rounded-lg border border-slate-200 leading-relaxed">
                      {rep?.agent_assessments?.specialist?.specialist_assessment ||
                        'Specialist clinical assessment completed.'}
                    </p>
                  </div>

                  {rep?.agent_assessments?.specialist?.diagnostic_recommendations && (
                    <div>
                      <h5 className="font-semibold text-slate-700 uppercase tracking-wider mb-2">
                        Specialist Recommendations:
                      </h5>
                      <ul className="list-disc pl-4 space-y-1 text-slate-700">
                        {rep.agent_assessments.specialist.diagnostic_recommendations.map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Critic Agent Output */}
              {selectedAgentKey === 'critic_agent' && (
                <div className="space-y-4 text-xs">
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <span className="text-slate-500 block mb-1">Verification Audit Summary:</span>
                    <p className="font-medium text-slate-800">
                      {rep?.critic_findings?.summary || 'Evidence verification complete.'}
                    </p>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="p-3 bg-emerald-50/60 border border-emerald-200 rounded-lg">
                      <span className="font-bold text-emerald-900 block mb-1">
                        ✓ Evidence-Supported Claims:
                      </span>
                      <ul className="space-y-1 text-emerald-800 text-[11px]">
                        {rep?.critic_findings?.supported_claims?.map((c, i) => (
                          <li key={i}>• {c}</li>
                        )) || <li>None noted</li>}
                      </ul>
                    </div>

                    <div className="p-3 bg-amber-50/60 border border-amber-200 rounded-lg">
                      <span className="font-bold text-amber-900 block mb-1">
                        ⚠️ Audit Flags & Gaps:
                      </span>
                      <ul className="space-y-1 text-amber-800 text-[11px]">
                        {rep?.critic_findings?.unsupported_claims?.map((c, i) => (
                          <li key={i}>• {c}</li>
                        ))}
                        {rep?.critic_findings?.missing_information?.map((m, i) => (
                          <li key={i}>• Missing: {m}</li>
                        ))}
                        {(!rep?.critic_findings?.unsupported_claims?.length &&
                          !rep?.critic_findings?.missing_information?.length) && (
                          <li>None flagged</li>
                        )}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {/* Synthesizer Output */}
              {selectedAgentKey === 'synthesizer' && (
                <div className="space-y-3 text-xs">
                  <p className="text-slate-700">
                    Compiled comprehensive 9-section Clinical Decision Support report with {rep?.differential_considerations?.length || 0} differential considerations.
                  </p>
                  <Button
                    size="sm"
                    variant="primary"
                    rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                    onClick={() => onNavigate('reports')}
                  >
                    Open Full Clinical Report
                  </Button>
                </div>
              )}
            </Card>
          </div>

          {/* Execution Event Logs (5 cols) */}
          <div className="lg:col-span-5 space-y-4">
            <Card
              title={
                <div className="flex items-center justify-between w-full">
                  <span>Execution Event Logs</span>
                  <span className="text-[11px] font-mono text-slate-400">
                    {logs.length} entries
                  </span>
                </div>
              }
              subtitle="Step-by-step agent actions and transitions"
            >
              {logs.length === 0 ? (
                <p className="text-xs text-slate-400 p-4 text-center">No agent logs recorded.</p>
              ) : (
                <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
                  {logs.map((logItem, idx) => {
                    const isExpanded = Boolean(expandedLogIndices[idx]);
                    return (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg border border-slate-200 bg-slate-50/70 text-xs space-y-1"
                      >
                        <div
                          className="flex items-center justify-between cursor-pointer"
                          onClick={() => toggleLogExpand(idx)}
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-[10px] text-slate-400">
                              #{idx + 1}
                            </span>
                            <span className="font-semibold text-slate-900">
                              {logItem.agent || 'Agent'}
                            </span>
                          </div>
                          <button className="text-slate-400 hover:text-slate-700">
                            {isExpanded ? (
                              <ChevronUp className="w-3.5 h-3.5" />
                            ) : (
                              <ChevronDown className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </div>
                        <p className="text-slate-600 text-[11px] leading-relaxed">
                          {logItem.action}
                        </p>

                        {isExpanded && (
                          <div className="mt-2 pt-2 border-t border-slate-200">
                            <pre className="text-[10px] font-mono bg-slate-900 text-slate-200 p-2 rounded overflow-x-auto">
                              {JSON.stringify(
                                Object.fromEntries(
                                  Object.entries(logItem).filter(
                                    ([k]) => !['agent', 'action'].includes(k)
                                  )
                                ),
                                null,
                                2
                              )}
                            </pre>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </Card>
          </div>
        </div>
      )}

      {!hasExecuted && (
        <Card className="p-10 text-center space-y-3">
          <GitBranch className="w-10 h-10 mx-auto text-slate-300" />
          <h3 className="text-sm font-semibold text-slate-700">
            No Active Multi-Agent Execution State
          </h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            The multi-agent workflow coordinates 6 specialized nodes with iterative critique loops. Enter patient findings in the Patient Workspace and execute the analysis to populate this trace.
          </p>
          <div className="pt-2">
            <Button size="sm" onClick={() => onNavigate('new-case')}>
              Go to Patient Workspace
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
};
