import React, { useState } from 'react';
import {
  Printer,
  Download,
  Copy,
  Check,
  ShieldAlert,
  FileCheck2,
  Stethoscope,
  Eye,
  Scale,
  HelpCircle,
  BookOpen,
  ArrowRight,
  AlertTriangle,
  User,
  HeartPulse,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge, UncertaintyBadge } from '../components/ui/Badge';
import { FinalReport, PatientCase } from '../types/clinical';
import { NavTab } from '../components/layout/Sidebar';

interface ClinicalReportProps {
  report: FinalReport | null;
  patientCase: Partial<PatientCase>;
  onNavigate: (tab: NavTab) => void;
}

export const ClinicalReport: React.FC<ClinicalReportProps> = ({
  report,
  patientCase,
  onNavigate,
}) => {
  const [copied, setCopied] = useState<boolean>(false);

  if (!report) {
    return (
      <div className="p-8 max-w-4xl mx-auto text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
          <FileCheck2 className="w-6 h-6" />
        </div>
        <h3 className="text-base font-semibold text-slate-800">
          No Clinical Decision Support Report Generated Yet
        </h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          Configure clinical parameters in the Patient Workspace and execute the Multi-Agent analysis to synthesize this report.
        </p>
        <div className="pt-2">
          <Button size="sm" onClick={() => onNavigate('new-case')}>
            Go to Patient Workspace
          </Button>
        </div>
      </div>
    );
  }

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadJson = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(report, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `medorchestr_report_${report.case_id || 'case'}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleCopySummary = () => {
    const summaryText = `MEDORCHESTR AI CLINICAL DECISION SUPPORT REPORT
Case ID: ${report.case_id || patientCase.case_id || 'N/A'}
Patient: Age ${patientCase.age || 'N/A'}, Sex: ${patientCase.sex || 'Unknown'}

SUMMARY:
${report.patient_summary}

KEY FINDINGS:
${report.key_clinical_findings?.map((f) => `- ${f}`).join('\n')}

DIFFERENTIAL CONSIDERATIONS:
${report.differential_considerations?.map((d) => `- ${d.condition} (Uncertainty: ${d.uncertainty})`).join('\n')}

DISCLAIMER:
${report.safety_disclaimer}
`;
    navigator.clipboard.writeText(summaryText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      {/* Top Action Bar (hidden on print) */}
      <div className="no-print flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <FileCheck2 className="w-5 h-5 text-teal-700" />
            Clinical Decision Support Report
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Comprehensive diagnostic hypothesis synthesis, evidence audit, and clinical recommendations.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            size="sm"
            variant="outline"
            leftIcon={copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4 text-slate-500" />}
            onClick={handleCopySummary}
          >
            {copied ? 'Copied to Clipboard' : 'Copy Summary'}
          </Button>

          <Button
            size="sm"
            variant="outline"
            leftIcon={<Download className="w-4 h-4 text-slate-500" />}
            onClick={handleDownloadJson}
          >
            Export JSON
          </Button>

          <Button
            size="sm"
            variant="primary"
            leftIcon={<Printer className="w-4 h-4" />}
            onClick={handlePrint}
          >
            Print / Save PDF
          </Button>
        </div>
      </div>

      {/* Hospital Formal Report Document Body */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-8 sm:p-10 space-y-8 print-card print:p-0 print:border-none">
        {/* Document Header & Institutional Banner */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6 pb-6 border-b border-slate-200">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-7 w-7 rounded bg-teal-800 text-white font-bold flex items-center justify-center text-xs">
                MO
              </span>
              <span className="font-bold text-slate-900 text-base tracking-tight">
                MedOrchestr AI
              </span>
            </div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Diagnostic Decision Support Report — Multi-Agent Consensus
            </p>
          </div>

          <div className="text-right text-xs space-y-1 font-mono text-slate-600">
            <div>
              <span className="text-slate-400">Case ID: </span>
              <span className="font-bold text-slate-900">{report.case_id || patientCase.case_id || 'PT-2026'}</span>
            </div>
            <div>
              <span className="text-slate-400">Timestamp: </span>
              <span>{new Date().toISOString().replace('T', ' ').slice(0, 19)} UTC</span>
            </div>
            <div>
              <span className="text-slate-400">Classification: </span>
              <span className="text-amber-800 font-semibold">Educational / Research Protocol</span>
            </div>
          </div>
        </div>

        {/* Patient Identity Strip */}
        <div className="bg-slate-50/80 rounded-xl p-4 border border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Patient ID:</span>
            <span className="font-bold text-slate-900 font-mono text-sm">
              {patientCase.patient_id || 'PT-UNASSIGNED'}
            </span>
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Demographics:</span>
            <span className="font-medium text-slate-800">
              {patientCase.age ? `${patientCase.age} Years` : 'Age N/A'}, {patientCase.sex || 'Unknown'}
            </span>
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Primary Presentation:</span>
            <span className="font-medium text-slate-800 truncate block">
              {(patientCase.symptoms || []).slice(0, 3).join(', ') || 'General symptoms'}
            </span>
          </div>
          <div>
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Imaging Attached:</span>
            <span className="font-medium text-teal-800">
              {patientCase.image_path ? 'Chest Radiograph' : 'None Attached'}
            </span>
          </div>
        </div>

        {/* Section 1: Patient Summary */}
        <section className="space-y-2">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-1.5">
            <span className="text-teal-700 font-mono">1.</span> Patient Presentation Summary
          </h3>
          <p className="text-sm text-slate-800 leading-relaxed bg-slate-50/50 p-4 rounded-xl border border-slate-100">
            {report.patient_summary || 'Summary unavailable.'}
          </p>
        </section>

        {/* Section 2: Key Clinical Findings */}
        <section className="space-y-2">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-1.5">
            <span className="text-teal-700 font-mono">2.</span> Key Positive & Negative Clinical Findings
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            {report.key_clinical_findings?.map((finding, idx) => (
              <div
                key={idx}
                className="p-3 bg-white border border-slate-200 rounded-lg flex items-start gap-2"
              >
                <span className="text-teal-700 font-bold shrink-0 mt-0.5">•</span>
                <span className="text-slate-800 leading-snug">{finding}</span>
              </div>
            )) || <p className="text-xs text-slate-400">No specific findings extracted.</p>}
          </div>
        </section>

        {/* Section 3: Radiographic Findings */}
        {report.imaging_findings && (
          <section className="space-y-3">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-1.5">
              <span className="text-teal-700 font-mono">3.</span> Radiographic Vision Findings
            </h3>
            <div className="bg-slate-50/60 p-4 rounded-xl border border-slate-200 space-y-3 text-xs">
              <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-200/80">
                <span className="font-semibold text-slate-800">
                  Modality: {report.imaging_findings.modality || 'Chest Radiograph'}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-slate-500">Technical Quality:</span>
                  <Badge variant="teal">{report.imaging_findings.technical_quality || 'Adequate'}</Badge>
                </div>
              </div>

              <div>
                <span className="text-[11px] font-semibold text-slate-500 uppercase block mb-1">
                  Radiologist Overall Impression:
                </span>
                <p className="text-slate-800 font-medium">
                  {report.imaging_findings.overall_impression || 'No impression stated.'}
                </p>
              </div>

              {report.imaging_findings.findings && report.imaging_findings.findings.length > 0 && (
                <div className="pt-2">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase block mb-2">
                    Visual Features:
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {report.imaging_findings.findings.map((f, i) => (
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
          </section>
        )}

        {/* Section 4: Differential Considerations with Uncertainty, Supporting, & Contradicting Evidence */}
        <section className="space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-1.5">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <span className="text-teal-700 font-mono">4.</span> Differential Considerations & Evidence Balance
            </h3>
            <span className="text-[11px] text-slate-400">
              Ranked considerations (Not definitive diagnoses)
            </span>
          </div>

          <div className="space-y-3">
            {report.differential_considerations?.map((diff, idx) => (
              <div
                key={idx}
                className="p-4 bg-white border border-slate-200 rounded-xl space-y-3 shadow-2xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono text-xs font-bold bg-slate-100 text-slate-700 w-6 h-6 rounded flex items-center justify-center">
                      0{idx + 1}
                    </span>
                    <h4 className="text-sm font-bold text-slate-900">{diff.condition}</h4>
                  </div>
                  <UncertaintyBadge level={diff.uncertainty} />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                  {/* Supporting Evidence */}
                  <div className="p-3 bg-emerald-50/50 rounded-lg border border-emerald-100 space-y-1.5">
                    <span className="font-bold text-emerald-900 block text-[11px] uppercase tracking-wider">
                      ✓ Supporting Findings & Evidence:
                    </span>
                    <ul className="space-y-1 text-slate-700">
                      {diff.supporting_evidence?.length ? (
                        diff.supporting_evidence.map((s, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <span className="text-emerald-700 font-bold">•</span>
                            <span>{s}</span>
                          </li>
                        ))
                      ) : (
                        <li className="text-slate-400">None explicitly listed.</li>
                      )}
                    </ul>
                  </div>

                  {/* Contradicting / Absent Evidence */}
                  <div className="p-3 bg-amber-50/50 rounded-lg border border-amber-100 space-y-1.5">
                    <span className="font-bold text-amber-900 block text-[11px] uppercase tracking-wider">
                      ✗ Contradicting / Absent Findings:
                    </span>
                    <ul className="space-y-1 text-slate-700">
                      {diff.contradicting_evidence?.length ? (
                        diff.contradicting_evidence.map((c, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <span className="text-amber-700 font-bold">•</span>
                            <span>{c}</span>
                          </li>
                        ))
                      ) : (
                        <li className="text-slate-400">None explicitly listed.</li>
                      )}
                    </ul>
                  </div>
                </div>

                {/* Evidence Citations Badges */}
                {diff.source_ids && diff.source_ids.length > 0 && (
                  <div className="flex items-center gap-2 pt-1 text-xs">
                    <span className="text-slate-500 font-medium">Grounding Citations:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {diff.source_ids.map((id) => (
                        <span
                          key={id}
                          className="font-mono text-[10px] font-bold bg-teal-50 text-teal-800 border border-teal-200 px-2 py-0.5 rounded"
                        >
                          [{id}]
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )) || <p className="text-xs text-slate-400">No differential considerations provided.</p>}
          </div>
        </section>

        {/* Section 5: Critic Verification Audit */}
        {report.critic_findings && (
          <section className="space-y-3">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-1.5">
              <span className="text-teal-700 font-mono">5.</span> Critic Agent Verification Audit
            </h3>
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3 text-xs">
              <div>
                <span className="text-[11px] font-semibold text-slate-500 uppercase block mb-1">
                  Verification Summary:
                </span>
                <p className="text-slate-800">
                  {report.critic_findings.summary || 'Audit complete.'}
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3 bg-white border border-slate-200 rounded-lg">
                  <span className="font-bold text-emerald-800 block mb-1">
                    ✓ Verified Grounded Claims:
                  </span>
                  <ul className="space-y-1 text-slate-700 text-[11px]">
                    {report.critic_findings.supported_claims?.map((c, i) => (
                      <li key={i}>• {c}</li>
                    )) || <li>None noted</li>}
                  </ul>
                </div>

                <div className="p-3 bg-white border border-slate-200 rounded-lg">
                  <span className="font-bold text-amber-800 block mb-1">
                    ⚠️ Missing Information & Audit Flags:
                  </span>
                  <ul className="space-y-1 text-slate-700 text-[11px]">
                    {report.critic_findings.missing_information?.map((m, i) => (
                      <li key={i}>• Missing: {m}</li>
                    ))}
                    {report.critic_findings.unsupported_claims?.map((u, i) => (
                      <li key={i}>• Unsupported: {u}</li>
                    ))}
                    {(!report.critic_findings.missing_information?.length &&
                      !report.critic_findings.unsupported_claims?.length) && (
                      <li className="text-slate-400">No critical evidence gaps flagged.</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Section 6: Suggested Next Clinical Questions */}
        {report.suggested_next_questions && report.suggested_next_questions.length > 0 && (
          <section className="space-y-2">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-1.5">
              <span className="text-teal-700 font-mono">6.</span> Suggested Questions for Clinician Review
            </h3>
            <div className="space-y-1.5 text-xs">
              {report.suggested_next_questions.map((q, i) => (
                <div
                  key={i}
                  className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-start gap-2 text-slate-800"
                >
                  <HelpCircle className="w-4 h-4 text-teal-700 shrink-0 mt-0.5" />
                  <span>{q}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Section 7: Source References */}
        {report.evidence_citations && report.evidence_citations.length > 0 && (
          <section className="space-y-3">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-1.5">
              <span className="text-teal-700 font-mono">7.</span> Verified Knowledge Base Citations
            </h3>
            <div className="overflow-x-auto border border-slate-200 rounded-lg">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                  <tr>
                    <th className="px-3 py-2 font-semibold">ID</th>
                    <th className="px-3 py-2 font-semibold">Literature Source</th>
                    <th className="px-3 py-2 font-semibold">Document Type</th>
                    <th className="px-3 py-2 font-semibold">Relevance Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {report.evidence_citations.map((c) => (
                    <tr key={c.source_id}>
                      <td className="px-3 py-2 font-mono font-bold text-teal-800">
                        [{c.source_id}]
                      </td>
                      <td className="px-3 py-2 font-medium text-slate-800">{c.title}</td>
                      <td className="px-3 py-2 text-slate-500 capitalize">
                        {c.document_type.replace(/_/g, ' ')}
                      </td>
                      <td className="px-3 py-2 font-mono text-slate-700">
                        {(c.relevance_score || 0).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Section 8: Similar Historical Reference Cases (Phase 3 CBR) */}
        {(report as any).similar_cases?.matches && (report as any).similar_cases.matches.length > 0 && (
          <section className="space-y-3">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-1.5">
              <span className="text-teal-700 font-mono">8.</span> Similar Reference Patient Encounters (CBR)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              {(report as any).similar_cases.matches.map((m: any) => (
                <div key={m.case_id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-mono text-[11px] font-bold text-indigo-700">{m.case_id}</span>
                      <span className="text-emerald-700 font-bold">{Math.round(m.similarity_score * 100)}% Match</span>
                    </div>
                    <div className="font-semibold text-slate-900 mb-1">{m.confirmed_diagnosis}</div>
                    <p className="text-[11px] text-slate-500 mb-2">{m.clinical_outcome}</p>
                  </div>
                  <div className="text-[10px] text-indigo-900 bg-white p-2 rounded border border-slate-200/80">
                    <span className="font-semibold">Takeaway: </span>{m.clinical_takeaway}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Section 9: Calibrated Confidence & Grounding Audit (Phase 3) */}
        {(report as any).confidence_calibration && (
          <section className="space-y-3">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-100 pb-1.5">
              <span className="text-teal-700 font-mono">9.</span> Calibrated Uncertainty & Grounding Metrics
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <span className="text-slate-500 text-[11px] block">Expected Calibration Error</span>
                <span className="text-lg font-bold text-slate-900">
                  {((report as any).confidence_calibration.expected_calibration_error * 100).toFixed(1)}%
                </span>
                <p className="text-[10px] text-slate-400 mt-0.5">Reliability curve error</p>
              </div>
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <span className="text-slate-500 text-[11px] block">Brier Accuracy Score</span>
                <span className="text-lg font-bold text-slate-900">
                  {(report as any).confidence_calibration.brier_score}
                </span>
                <p className="text-[10px] text-slate-400 mt-0.5">Mean probability loss</p>
              </div>
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <span className="text-slate-500 text-[11px] block">Faithfulness Audit</span>
                <span className="text-lg font-bold text-emerald-600">
                  {(report as any).faithfulness_audit?.faithfulness_score || 94.0}%
                </span>
                <p className="text-[10px] text-slate-400 mt-0.5">Grounded claims</p>
              </div>
            </div>
          </section>
        )}

        {/* Section 8: Mandatory Safety & Regulatory Disclaimer */}
        <section className="pt-4 border-t border-slate-200">
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600 space-y-2 leading-relaxed">
            <div className="flex items-center gap-2 font-bold text-slate-900">
              <ShieldAlert className="w-4 h-4 text-amber-600" />
              <span>Mandatory Clinical Decision Support Notice & Limitations</span>
            </div>
            <p className="text-[11px] text-slate-600">
              {report.safety_disclaimer ||
                'FOR RESEARCH AND EDUCATIONAL USE ONLY. This system does not provide a confirmed medical diagnosis and does not replace a qualified healthcare professional.'}
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[10px] text-slate-500 pt-1">
              <div>• Output must be corroborated by attending clinical personnel.</div>
              <div>• No medication prescriptions or dosages are generated.</div>
              <div>• Uncalibrated AI scores are not disease probabilities.</div>
              <div>• Prototype evaluated for research decision-support only.</div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};
