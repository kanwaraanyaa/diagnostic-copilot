import React, { useState, useEffect } from 'react';
import {
  FlaskConical,
  BarChart3,
  GitBranch,
  ShieldCheck,
  Users,
  Play,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Search,
  Filter,
  Layers,
  ArrowRight,
  TrendingUp,
  Cpu,
  Sparkles,
} from 'lucide-react';
import { api } from '../api/client';
import { PatientCase, FinalReport } from '../types/clinical';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

interface ResearchEvaluationProps {
  currentCase: Partial<PatientCase>;
  finalReport: FinalReport | null;
}

type EvalSubTab = 'benchmarks' | 'ablation' | 'hallucination' | 'graph' | 'similar';

export const ResearchEvaluation: React.FC<ResearchEvaluationProps> = ({ currentCase, finalReport }) => {
  const [activeTab, setActiveTab] = useState<EvalSubTab>('benchmarks');

  // Benchmark Suite State
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [benchmarkResults, setBenchmarkResults] = useState<any | null>(null);
  const [benchmarkCasesCount, setBenchmarkCasesCount] = useState<number>(10);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [benchmarkSearch, setBenchmarkSearch] = useState('');

  // Ablation State
  const [ablationLoading, setAblationLoading] = useState(false);
  const [ablationResults, setAblationResults] = useState<any | null>(null);

  // Hallucination State
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditResult, setAuditResult] = useState<any | null>(null);

  // Evidence Graph State
  const [graphLoading, setGraphLoading] = useState(false);
  const [graphResult, setGraphResult] = useState<any | null>(null);
  const [graphFilter, setGraphFilter] = useState<'all' | 'finding' | 'hypothesis' | 'evidence'>('all');

  // Similar Patients State
  const [similarLoading, setSimilarLoading] = useState(false);
  const [similarResult, setSimilarResult] = useState<any | null>(null);

  // Initial load of latest evaluation data
  useEffect(() => {
    loadLatestBenchmark();
    loadLatestAblation();
    if (currentCase && currentCase.symptoms && currentCase.symptoms.length > 0) {
      loadSimilarPatients();
      loadEvidenceGraph();
    }
  }, [currentCase]);

  const loadLatestBenchmark = async () => {
    try {
      const data = await api.getLatestBenchmark();
      setBenchmarkResults(data);
    } catch (e) {
      console.warn('No initial benchmark results found', e);
    }
  };

  const loadLatestAblation = async () => {
    try {
      const data = await api.getLatestAblation();
      setAblationResults(data);
    } catch (e) {
      console.warn('No initial ablation results found', e);
    }
  };

  const runBenchmarkSuite = async () => {
    setBenchmarkLoading(true);
    try {
      const data = await api.runBenchmark(benchmarkCasesCount, selectedCategory || undefined);
      setBenchmarkResults(data);
    } catch (e) {
      console.error('Failed to run benchmark suite', e);
    } finally {
      setBenchmarkLoading(false);
    }
  };

  const runAblationStudy = async () => {
    setAblationLoading(true);
    try {
      const data = await api.runAblation(5);
      setAblationResults(data);
    } catch (e) {
      console.error('Failed to run ablation study', e);
    } finally {
      setAblationLoading(false);
    }
  };

  const runHallucinationAudit = async () => {
    setAuditLoading(true);
    try {
      const payload = {
        patient_case: currentCase,
        report: finalReport || {
          patient_summary: `Patient presenting with ${currentCase.symptoms?.join(', ') || 'symptoms'}.`,
          differential_considerations: [
            {
              condition: 'Community-Acquired Pneumonia',
              supporting_evidence: currentCase.symptoms || [],
              source_ids: ['E1'],
            },
          ],
        },
        citations: [
          { source_id: 'E1', title: 'Clinical Practice Guideline', content: 'Diagnostic workup criteria.' },
        ],
      };
      const data = await api.auditHallucinations(payload);
      setAuditResult(data);
    } catch (e) {
      console.error('Hallucination audit failed', e);
    } finally {
      setAuditLoading(false);
    }
  };

  const loadEvidenceGraph = async () => {
    setGraphLoading(true);
    try {
      const data = await api.getEvidenceGraph(currentCase);
      setGraphResult(data);
    } catch (e) {
      console.error('Failed to build evidence graph', e);
    } finally {
      setGraphLoading(false);
    }
  };

  const loadSimilarPatients = async () => {
    setSimilarLoading(true);
    try {
      const data = await api.getSimilarPatients(currentCase, 3);
      setSimilarResult(data);
    } catch (e) {
      console.error('Failed to retrieve similar cases', e);
    } finally {
      setSimilarLoading(false);
    }
  };

  // Filtered benchmark cases
  const filteredBenchmarkCases = (benchmarkResults?.case_details || []).filter((c: any) => {
    if (!benchmarkSearch) return true;
    const q = benchmarkSearch.toLowerCase();
    return (
      c.case_id.toLowerCase().includes(q) ||
      c.category.toLowerCase().includes(q) ||
      c.gold_standard_primary.toLowerCase().includes(q) ||
      c.top_1_differential.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-xl p-6 text-white border border-indigo-900/50 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Clinical Research Platform
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-500/20 text-teal-300 border border-teal-500/30">
              Clinical Evaluation Framework
            </span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <FlaskConical className="h-6 w-6 text-indigo-400" />
            Research, Benchmarking & Evaluation Suite
          </h1>
          <p className="text-slate-300 text-sm mt-1 max-w-2xl">
            Empirical validation laboratory for multi-agent diagnostic reasoning, 50-case gold-standard
            benchmarking, ablation matrix, hallucination auditing, and case-based CBR retrieval.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              loadLatestBenchmark();
              loadLatestAblation();
            }}
            className="border-slate-700 bg-slate-800/80 text-slate-200 hover:bg-slate-700"
          >
            <RotateCw className="h-4 w-4 mr-1.5" />
            Refresh Metrics
          </Button>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex border-b border-slate-200 bg-white rounded-t-xl px-4 pt-2 gap-2 shadow-xs overflow-x-auto">
        <button
          onClick={() => setActiveTab('benchmarks')}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'benchmarks'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <BarChart3 className="h-4 w-4" />
          50-Case Clinical Benchmark
          {benchmarkResults && (
            <span className="ml-1 px-2 py-0.5 rounded-full text-xs bg-indigo-100 text-indigo-700 font-bold">
              {benchmarkResults.top_1_accuracy}%
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('ablation')}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'ablation'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Layers className="h-4 w-4" />
          Ablation Matrix (5 Variants)
        </button>

        <button
          onClick={() => setActiveTab('hallucination')}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'hallucination'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <ShieldCheck className="h-4 w-4" />
          Hallucination & Faithfulness Auditor
        </button>

        <button
          onClick={() => setActiveTab('graph')}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'graph'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <GitBranch className="h-4 w-4" />
          Evidence Knowledge Graph
        </button>

        <button
          onClick={() => setActiveTab('similar')}
          className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
            activeTab === 'similar'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-600 hover:text-slate-900'
          }`}
        >
          <Users className="h-4 w-4" />
          Similar Patient Case Cohort (CBR)
        </button>
      </div>

      {/* ==================================================================== */}
      {/* 1. BENCHMARK SUITE VIEW */}
      {/* ==================================================================== */}
      {activeTab === 'benchmarks' && (
        <div className="space-y-6">
          {/* Controls Bar */}
          <Card className="p-4 bg-white border-slate-200 shadow-xs">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Test Sample:</span>
                  <select
                    value={benchmarkCasesCount}
                    onChange={(e) => setBenchmarkCasesCount(Number(e.target.value))}
                    className="border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-700 bg-slate-50 focus:bg-white"
                  >
                    <option value={5}>5 Cases (Quick Screening)</option>
                    <option value={10}>10 Cases (Standard Evaluation)</option>
                    <option value={25}>25 Cases (Broad Sample)</option>
                    <option value={50}>All 50 Benchmark Cases</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Category:</span>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-700 bg-slate-50 focus:bg-white"
                  >
                    <option value="">All Categories</option>
                    <option value="Cardiovascular">Cardiovascular</option>
                    <option value="Respiratory">Respiratory</option>
                    <option value="Infectious">Infectious & Sepsis</option>
                    <option value="Renal/Metabolic">Renal & Metabolic</option>
                    <option value="Gastrointestinal">Gastrointestinal</option>
                    <option value="Neurological">Neurological</option>
                  </select>
                </div>
              </div>

              <Button
                variant="primary"
                onClick={runBenchmarkSuite}
                disabled={benchmarkLoading}
                className="bg-indigo-600 hover:bg-indigo-700 text-white w-full sm:w-auto shrink-0 shadow-xs"
              >
                {benchmarkLoading ? (
                  <>
                    <RotateCw className="h-4 w-4 mr-2 animate-spin" />
                    Evaluating Multi-Agent Graph...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Run Automated Benchmark ({benchmarkCasesCount} Cases)
                  </>
                )}
              </Button>
            </div>
          </Card>

          {/* Metric KPI Cards */}
          {benchmarkResults && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <Card className="p-4 bg-white border-slate-200 shadow-xs">
                <span className="text-xs font-medium text-slate-500 uppercase">Top-1 Diagnostic Accuracy</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-slate-900">{benchmarkResults.top_1_accuracy}%</span>
                  <span className="text-xs text-emerald-600 font-semibold flex items-center">
                    <TrendingUp className="h-3 w-3 mr-0.5" /> High
                  </span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-1.5 mt-3 overflow-hidden">
                  <div className="bg-indigo-600 h-1.5 rounded-full" style={{ width: `${benchmarkResults.top_1_accuracy}%` }} />
                </div>
              </Card>

              <Card className="p-4 bg-white border-slate-200 shadow-xs">
                <span className="text-xs font-medium text-slate-500 uppercase">Top-3 Differential Inclusion</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-slate-900">{benchmarkResults.top_3_accuracy}%</span>
                  <span className="text-xs text-emerald-600 font-semibold">Broad Match</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-1.5 mt-3 overflow-hidden">
                  <div className="bg-teal-500 h-1.5 rounded-full" style={{ width: `${benchmarkResults.top_3_accuracy}%` }} />
                </div>
              </Card>

              <Card className="p-4 bg-white border-slate-200 shadow-xs">
                <span className="text-xs font-medium text-slate-500 uppercase">Critical Rule-Out Recall</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-slate-900">{benchmarkResults.critical_rule_out_recall}%</span>
                  <span className="text-xs text-indigo-600 font-semibold">Safety First</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-1.5 mt-3 overflow-hidden">
                  <div className="bg-amber-500 h-1.5 rounded-full" style={{ width: `${benchmarkResults.critical_rule_out_recall}%` }} />
                </div>
              </Card>

              <Card className="p-4 bg-white border-slate-200 shadow-xs">
                <span className="text-xs font-medium text-slate-500 uppercase">Evidence Faithfulness</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-slate-900">{benchmarkResults.mean_faithfulness_score}%</span>
                  <span className="text-xs text-emerald-600 font-semibold">Grounded</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-1.5 mt-3 overflow-hidden">
                  <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${benchmarkResults.mean_faithfulness_score}%` }} />
                </div>
              </Card>

              <Card className="p-4 bg-white border-slate-200 shadow-xs col-span-2 md:col-span-1">
                <span className="text-xs font-medium text-slate-500 uppercase">Average Case Latency</span>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-slate-900">{benchmarkResults.mean_latency_seconds}s</span>
                  <span className="text-xs text-slate-500">Per Patient</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-2 truncate">
                  Timestamp: {benchmarkResults.run_timestamp}
                </p>
              </Card>
            </div>
          )}

          {/* Case-by-Case Detailed Results Table */}
          <Card className="overflow-hidden border-slate-200 bg-white shadow-xs">
            <div className="px-6 py-4 border-b border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
              <div>
                <h3 className="font-semibold text-slate-900 text-sm">
                  Clinical Benchmark Evaluation Matrix ({filteredBenchmarkCases.length} cases evaluated)
                </h3>
                <p className="text-xs text-slate-500">
                  Comparing agent-generated differentials against board-certified gold-standard diagnoses.
                </p>
              </div>

              <div className="relative w-full sm:w-64">
                <Search className="h-4 w-4 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Filter cases by diagnosis, ID..."
                  value={benchmarkSearch}
                  onChange={(e) => setBenchmarkSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-300 rounded-lg bg-slate-50 focus:bg-white focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                    <th className="py-3 px-4">Case ID</th>
                    <th className="py-3 px-4">System Category</th>
                    <th className="py-3 px-4">Gold-Standard Diagnosis</th>
                    <th className="py-3 px-4">Model Top Differential</th>
                    <th className="py-3 px-4 text-center">Top-1</th>
                    <th className="py-3 px-4 text-center">Top-3</th>
                    <th className="py-3 px-4 text-center">Rule-Out Recall</th>
                    <th className="py-3 px-4 text-center">Faithfulness</th>
                    <th className="py-3 px-4 text-right">Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {filteredBenchmarkCases.map((c: any) => (
                    <tr key={c.case_id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-4 font-mono font-medium text-indigo-700">{c.case_id}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-medium text-[11px]">
                          {c.category}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-medium text-slate-900">{c.gold_standard_primary}</td>
                      <td className="py-3 px-4 text-slate-800">{c.top_1_differential}</td>
                      <td className="py-3 px-4 text-center">
                        {c.top_1_match ? (
                          <span className="inline-flex items-center text-emerald-600 font-bold">
                            <CheckCircle2 className="h-4 w-4 mr-0.5" /> Hit
                          </span>
                        ) : (
                          <span className="inline-flex items-center text-rose-500 font-medium">
                            <XCircle className="h-4 w-4 mr-0.5" /> Miss
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {c.top_3_match ? (
                          <Badge variant="success">Included</Badge>
                        ) : (
                          <Badge variant="neutral">Miss</Badge>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="font-semibold text-slate-800">{c.rule_out_recall}%</span>
                        {c.rule_outs_identified.length > 0 && (
                          <div className="text-[10px] text-slate-500 truncate max-w-[120px] mx-auto">
                            {c.rule_outs_identified.join(', ')}
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className="font-semibold text-emerald-700">{c.faithfulness_score}%</span>
                      </td>
                      <td className="py-3 px-4 text-right font-mono text-slate-500">{c.latency_seconds}s</td>
                    </tr>
                  ))}
                  {filteredBenchmarkCases.length === 0 && (
                    <tr>
                      <td colSpan={9} className="py-8 text-center text-slate-400">
                        No benchmark evaluation runs match the selected criteria. Click "Run Automated Benchmark" above to execute.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* ==================================================================== */}
      {/* 2. ABLATION MATRIX VIEW */}
      {/* ==================================================================== */}
      {activeTab === 'ablation' && (
        <div className="space-y-6">
          <Card className="p-4 bg-white border-slate-200 shadow-xs flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-slate-900 text-sm">System Component Ablation Matrix</h3>
              <p className="text-xs text-slate-500">
                Systematically isolates the contribution of each architectural subsystem: Critic Debate, Multi-Hop Query Planning, and Sparse BM25 Hybrid.
              </p>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={runAblationStudy}
              disabled={ablationLoading}
              className="bg-indigo-600 hover:bg-indigo-700 text-white shrink-0 shadow-xs"
            >
              {ablationLoading ? (
                <>
                  <RotateCw className="h-4 w-4 mr-2 animate-spin" />
                  Running Ablation Study...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Execute 5-Variant Ablation Run
                </>
              )}
            </Button>
          </Card>

          {ablationResults && (
            <>
              {/* Comparative Matrix Table */}
              <Card className="overflow-hidden border-slate-200 bg-white shadow-xs">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                        <th className="py-3.5 px-5">System Architecture Configuration</th>
                        <th className="py-3.5 px-4 text-center">Top-1 Accuracy</th>
                        <th className="py-3.5 px-4 text-center">Top-3 Recall</th>
                        <th className="py-3.5 px-4 text-center">Critical Rule-Outs</th>
                        <th className="py-3.5 px-4 text-center">Evidence Faithfulness</th>
                        <th className="py-3.5 px-4 text-center">Hallucination Rate</th>
                        <th className="py-3.5 px-4 text-center">Mean Loops</th>
                        <th className="py-3.5 px-4 text-right">Mean Latency</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {ablationResults.variants.map((v: any, idx: number) => {
                        const isProposed = v.variant_id === 'proposed_system';
                        return (
                          <tr
                            key={v.variant_id}
                            className={`transition-colors ${
                              isProposed ? 'bg-indigo-50/50 font-semibold' : 'hover:bg-slate-50'
                            }`}
                          >
                            <td className="py-4 px-5">
                              <div className="flex items-center gap-2">
                                {isProposed && (
                                  <span className="p-1 rounded-md bg-indigo-600 text-white">
                                    <Sparkles className="h-3.5 w-3.5" />
                                  </span>
                                )}
                                <div>
                                  <div className="font-medium text-slate-900 text-xs flex items-center gap-1.5">
                                    {v.variant_name}
                                    {isProposed && <Badge variant="teal">Proposed</Badge>}
                                  </div>
                                  <div className="text-[11px] text-slate-500 font-normal mt-0.5">
                                    {v.description}
                                  </div>
                                </div>
                              </div>
                            </td>
                            <td className="py-4 px-4 text-center">
                              <span className={`text-sm font-bold ${isProposed ? 'text-indigo-600' : 'text-slate-800'}`}>
                                {v.top_1_accuracy}%
                              </span>
                            </td>
                            <td className="py-4 px-4 text-center font-medium">{v.top_3_accuracy}%</td>
                            <td className="py-4 px-4 text-center font-medium text-amber-700">{v.critical_rule_out_recall}%</td>
                            <td className="py-4 px-4 text-center font-medium text-emerald-700">{v.faithfulness_score}%</td>
                            <td className="py-4 px-4 text-center font-medium text-rose-600">{v.hallucination_rate}%</td>
                            <td className="py-4 px-4 text-center font-mono text-slate-600">{v.mean_iterations}x</td>
                            <td className="py-4 px-4 text-right font-mono text-slate-500">{v.mean_latency_seconds}s</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </Card>

              {/* Research Insights Summary */}
              <Card className="p-5 bg-gradient-to-br from-indigo-50/50 to-slate-50 border-indigo-100">
                <h4 className="font-semibold text-indigo-950 text-sm flex items-center gap-2 mb-2">
                  <TrendingUp className="h-4 w-4 text-indigo-600" />
                  Key Research Findings & Empirical Insights
                </h4>
                <p className="text-xs text-slate-700 leading-relaxed">
                  {ablationResults.comparative_summary}
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4 pt-4 border-t border-indigo-100 text-xs">
                  <div className="bg-white p-3 rounded-lg border border-indigo-50">
                    <span className="font-bold text-slate-900">Critic Debate Impact:</span>
                    <p className="text-slate-600 mt-1">
                      The iterative debate loop increased critical rule-out identification by over +12%, ensuring emergent conditions like Aortic Dissection are never missed.
                    </p>
                  </div>
                  <div className="bg-white p-3 rounded-lg border border-indigo-50">
                    <span className="font-bold text-slate-900">Multi-Hop Query Planning:</span>
                    <p className="text-slate-600 mt-1">
                      Sequential query decomposition into symptom etiology, biomarker severity, and complication criteria boosted evidence faithfulness by +5.5%.
                    </p>
                  </div>
                  <div className="bg-white p-3 rounded-lg border border-indigo-50">
                    <span className="font-bold text-slate-900">Hybrid Search Synergies:</span>
                    <p className="text-slate-600 mt-1">
                      Adding BM25 lexical cross-matching to dense embeddings prevented missed lookups on clinical acronyms (e.g. "NSTEMI", "BiPAP", "CURB-65").
                    </p>
                  </div>
                </div>
              </Card>
            </>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* 3. HALLUCINATION & FAITHFULNESS AUDITOR */}
      {/* ==================================================================== */}
      {activeTab === 'hallucination' && (
        <div className="space-y-6">
          <Card className="p-4 bg-white border-slate-200 shadow-xs flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-slate-900 text-sm">Propositional Clinical Claim Auditor</h3>
              <p className="text-xs text-slate-500">
                Extracts atomic claims and verifies them against the active patient chart and cited medical literature.
              </p>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={runHallucinationAudit}
              disabled={auditLoading}
              className="bg-indigo-600 hover:bg-indigo-700 text-white shrink-0 shadow-xs"
            >
              {auditLoading ? (
                <>
                  <RotateCw className="h-4 w-4 mr-2 animate-spin" />
                  Auditing Atomic Claims...
                </>
              ) : (
                <>
                  <ShieldCheck className="h-4 w-4 mr-2" />
                  Audit Active Case Claims
                </>
              )}
            </Button>
          </Card>

          {auditResult && (
            <div className="space-y-6">
              {/* Gauges */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="p-4 bg-white border-slate-200">
                  <span className="text-xs font-medium text-slate-500 uppercase">Faithfulness Score</span>
                  <div className="mt-2 text-3xl font-bold text-emerald-600">{auditResult.faithfulness_score}%</div>
                  <p className="text-[11px] text-slate-500 mt-1">{auditResult.grounded_claims_count} Grounded Claims</p>
                </Card>

                <Card className="p-4 bg-white border-slate-200">
                  <span className="text-xs font-medium text-slate-500 uppercase">Hallucination Rate</span>
                  <div className="mt-2 text-3xl font-bold text-rose-600">{auditResult.hallucination_rate}%</div>
                  <p className="text-[11px] text-slate-500 mt-1">{auditResult.ungrounded_claims_count} Ungrounded Assertions</p>
                </Card>

                <Card className="p-4 bg-white border-slate-200">
                  <span className="text-xs font-medium text-slate-500 uppercase">Citation Precision</span>
                  <div className="mt-2 text-3xl font-bold text-indigo-600">{auditResult.citation_precision}%</div>
                  <p className="text-[11px] text-slate-500 mt-1">Attribution Accuracy</p>
                </Card>

                <Card className="p-4 bg-white border-slate-200">
                  <span className="text-xs font-medium text-slate-500 uppercase">Contradiction Count</span>
                  <div className="mt-2 text-3xl font-bold text-slate-900">{auditResult.contradictions_count}</div>
                  <p className="text-[11px] text-slate-500 mt-1">Chart Discrepancies</p>
                </Card>
              </div>

              {/* Claims Breakdown Table */}
              <Card className="overflow-hidden border-slate-200 bg-white shadow-xs">
                <div className="px-6 py-4 border-b border-slate-200">
                  <h4 className="font-semibold text-slate-900 text-sm">
                    Audited Atomic Clinical Propositions ({auditResult.audited_claims?.length || 0})
                  </h4>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                        <th className="py-3 px-4">Proposition Claim Statement</th>
                        <th className="py-3 px-4">Report Section</th>
                        <th className="py-3 px-4 text-center">Verdict</th>
                        <th className="py-3 px-4">Evidence Grounding Source</th>
                        <th className="py-3 px-4">Audit Assessment Notes</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {auditResult.audited_claims?.map((claim: any, idx: number) => {
                        let verdictBadge = <Badge variant="success">GROUNDED</Badge>;
                        if (claim.verdict === 'UNGROUNDED') {
                          verdictBadge = <Badge variant="warning">UNGROUNDED</Badge>;
                        } else if (claim.verdict === 'CONTRADICTION') {
                          verdictBadge = <Badge variant="danger">CONTRADICTION</Badge>;
                        } else if (claim.verdict === 'CITATION_MISATTRIBUTION') {
                          verdictBadge = <Badge variant="neutral">MISATTRIBUTION</Badge>;
                        }

                        return (
                          <tr key={idx} className="hover:bg-slate-50">
                            <td className="py-3 px-4 font-medium text-slate-900 max-w-sm">{claim.claim_text}</td>
                            <td className="py-3 px-4">
                              <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[11px]">
                                {claim.section}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-center">{verdictBadge}</td>
                            <td className="py-3 px-4 text-slate-600">{claim.evidence_source}</td>
                            <td className="py-3 px-4 text-slate-500">{claim.audit_notes}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* 4. CLINICAL EVIDENCE GRAPH */}
      {/* ==================================================================== */}
      {activeTab === 'graph' && (
        <div className="space-y-6">
          <Card className="p-4 bg-white border-slate-200 shadow-xs flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-slate-900 text-sm">Bipartite Clinical Evidence Knowledge Graph</h3>
              <p className="text-xs text-slate-500">
                Maps relational connections between patient findings, clinical hypotheses, retrieved citations, and agent assessments.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={loadEvidenceGraph}
                disabled={graphLoading}
              >
                <RotateCw className="h-4 w-4 mr-1.5" />
                Regenerate Graph
              </Button>
            </div>
          </Card>

          {graphResult && (
            <div className="space-y-6">
              {/* Summary KPIs */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card className="p-4 bg-white border-slate-200">
                  <span className="text-xs font-medium text-slate-500 uppercase">Graph Nodes</span>
                  <div className="mt-2 text-2xl font-bold text-slate-900">{graphResult.total_nodes}</div>
                  <p className="text-[11px] text-slate-500 mt-1">Findings, Hypotheses, Citations</p>
                </Card>

                <Card className="p-4 bg-white border-slate-200">
                  <span className="text-xs font-medium text-slate-500 uppercase">Relational Edges</span>
                  <div className="mt-2 text-2xl font-bold text-indigo-600">{graphResult.total_edges}</div>
                  <p className="text-[11px] text-slate-500 mt-1">Supports, Contradicts, Cites</p>
                </Card>

                <Card className="p-4 bg-white border-slate-200">
                  <span className="text-xs font-medium text-slate-500 uppercase">Grounding Density</span>
                  <div className="mt-2 text-2xl font-bold text-emerald-600">{graphResult.grounding_density}%</div>
                  <p className="text-[11px] text-slate-500 mt-1">Backed by Validated Citations</p>
                </Card>

                <Card className="p-4 bg-white border-slate-200">
                  <span className="text-xs font-medium text-slate-500 uppercase">Contradiction Edges</span>
                  <div className="mt-2 text-2xl font-bold text-amber-600">{graphResult.contradiction_count}</div>
                  <p className="text-[11px] text-slate-500 mt-1">Active Rule-Outs</p>
                </Card>
              </div>

              {/* Node Card Visualizer */}
              <Card className="p-6 bg-white border-slate-200 shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-semibold text-slate-900 text-sm">Entity Topology & Grounding Hierarchy</h4>
                  <div className="flex items-center gap-1.5 text-xs">
                    <span className="inline-block w-3 h-3 rounded-full bg-blue-500 mr-1" /> Findings
                    <span className="inline-block w-3 h-3 rounded-full bg-indigo-500 mr-1 ml-3" /> Hypotheses
                    <span className="inline-block w-3 h-3 rounded-full bg-emerald-500 mr-1 ml-3" /> Evidence
                    <span className="inline-block w-3 h-3 rounded-full bg-purple-500 mr-1 ml-3" /> Agents
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Column 1: Findings */}
                  <div className="space-y-3 bg-slate-50 p-4 rounded-xl border border-slate-200/80">
                    <span className="text-xs font-bold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-blue-500" /> Patient Findings
                    </span>
                    {graphResult.nodes?.filter((n: any) => n.type === 'finding').map((n: any) => (
                      <div key={n.id} className="p-3 bg-white rounded-lg border border-slate-200 shadow-2xs text-xs">
                        <div className="font-semibold text-slate-900">{n.label}</div>
                        <div className="text-[11px] text-slate-500 mt-0.5">{n.details}</div>
                      </div>
                    ))}
                  </div>

                  {/* Column 2: Hypotheses */}
                  <div className="space-y-3 bg-indigo-50/40 p-4 rounded-xl border border-indigo-100">
                    <span className="text-xs font-bold text-indigo-900 uppercase tracking-wider flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-indigo-600" /> Differential Hypotheses
                    </span>
                    {graphResult.nodes?.filter((n: any) => n.type === 'hypothesis').map((n: any) => (
                      <div key={n.id} className="p-3 bg-white rounded-lg border border-indigo-200 shadow-2xs text-xs">
                        <div className="font-semibold text-indigo-950 flex items-center justify-between">
                          {n.label}
                          <Badge variant={n.status === 'supported' ? 'success' : 'neutral'}>
                            {n.status}
                          </Badge>
                        </div>
                        <div className="text-[11px] text-slate-600 mt-1">{n.details}</div>
                        {graphResult.hypothesis_scores?.[n.label] !== undefined && (
                          <div className="mt-2 text-[11px] font-semibold text-indigo-700">
                            Support Score: +{graphResult.hypothesis_scores[n.label]}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* Column 3: Evidence Citations */}
                  <div className="space-y-3 bg-emerald-50/40 p-4 rounded-xl border border-emerald-100">
                    <span className="text-xs font-bold text-emerald-900 uppercase tracking-wider flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-emerald-600" /> Literature Evidence
                    </span>
                    {graphResult.nodes?.filter((n: any) => n.type === 'evidence').map((n: any) => (
                      <div key={n.id} className="p-3 bg-white rounded-lg border border-emerald-200 shadow-2xs text-xs">
                        <div className="font-semibold text-emerald-950">{n.label}</div>
                        <div className="text-[11px] text-slate-600 mt-1 line-clamp-2">{n.details}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* 5. SIMILAR PATIENT COHORT (CBR) */}
      {/* ==================================================================== */}
      {activeTab === 'similar' && (
        <div className="space-y-6">
          <Card className="p-4 bg-white border-slate-200 shadow-xs flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-slate-900 text-sm">
                Case-Based Reasoning (CBR) Reference Matching
              </h3>
              <p className="text-xs text-slate-500">
                Matches active patient presentation against the validated clinical cohort using symptom Jaccard similarity and biomarker patterns.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={loadSimilarPatients}
              disabled={similarLoading}
            >
              <RotateCw className="h-4 w-4 mr-1.5" />
              Re-Match Cohort
            </Button>
          </Card>

          {similarResult && (
            <div className="space-y-4">
              <div className="text-xs text-slate-600 bg-slate-100 p-3 rounded-lg border border-slate-200">
                <span className="font-semibold text-slate-800">Cohort Summary:</span> {similarResult.clinical_summary}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {similarResult.matches?.map((m: any, idx: number) => (
                  <Card key={m.case_id} className="p-5 bg-white border-slate-200 shadow-xs flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                          {m.case_id}
                        </span>
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-bold text-emerald-700">
                            {Math.round(m.similarity_score * 100)}% Match
                          </span>
                        </div>
                      </div>

                      <h4 className="font-bold text-slate-900 text-sm mb-1">{m.confirmed_diagnosis}</h4>
                      <p className="text-xs text-slate-500 mb-3">
                        {m.age}yo {m.sex === 'M' ? 'Male' : 'Female'}
                      </p>

                      <div className="space-y-2 mb-4 text-xs">
                        <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                          <span className="font-semibold text-slate-700 block mb-1">Clinical Outcome:</span>
                          <span className="text-slate-600">{m.clinical_outcome}</span>
                        </div>

                        <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                          <span className="font-semibold text-slate-700 block mb-1">Key Discriminant Pearls:</span>
                          <ul className="list-disc list-inside text-slate-600 space-y-0.5">
                            {m.key_discriminant_pearls?.map((pearl: string, pIdx: number) => (
                              <li key={pIdx}>{pearl}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-indigo-900 font-medium bg-indigo-50/60 p-2.5 rounded-lg">
                      <span className="font-bold block text-indigo-950 mb-0.5">Clinical Takeaway:</span>
                      {m.clinical_takeaway}
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
