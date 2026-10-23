import React, { useState } from 'react';
import {
  User,
  AlertTriangle,
  Plus,
  Trash2,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  ImageIcon,
  Sparkles,
  Layers,
  HeartPulse,
  Pill,
  ShieldCheck,
  Stethoscope,
  TestTube2,
  FileCheck2,
  Save,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Input, Textarea, Select } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import { LabResult, Medication, PatientCase, Sex } from '../types/clinical';
import { COMMON_LAB_TEMPLATES } from '../data/demoCase';
import { api } from '../api/client';

interface PatientWorkspaceProps {
  currentCase: Partial<PatientCase>;
  onChangeCase: (updated: Partial<PatientCase>) => void;
  onRunAnalysis: (mode: 'agentic' | 'baseline') => Promise<void>;
  isAnalyzing: boolean;
  onNavigateToImaging: () => void;
  isDemoLoaded: boolean;
}

const COMMON_SYMPTOM_TAGS = [
  'fever',
  'productive cough',
  'dry cough',
  'shortness of breath',
  'pleuritic chest pain',
  'fatigue',
  'chills',
  'hemoptysis',
  'orthopnea',
  'diaphoresis',
];

const SECTIONS = [
  { id: 1, label: 'Demographics', icon: User },
  { id: 2, label: 'Presenting Complaints', icon: Stethoscope },
  { id: 3, label: 'Medical History', icon: Layers },
  { id: 4, label: 'Medications', icon: Pill },
  { id: 5, label: 'Allergies', icon: AlertTriangle },
  { id: 6, label: 'Vital Signs', icon: HeartPulse },
  { id: 7, label: 'Laboratory Findings', icon: TestTube2 },
  { id: 8, label: 'Clinical Notes & Exam', icon: Stethoscope },
  { id: 9, label: 'Medical Imaging', icon: ImageIcon },
  { id: 10, label: 'Review & Submit', icon: FileCheck2 },
];

export const PatientWorkspace: React.FC<PatientWorkspaceProps> = ({
  currentCase,
  onChangeCase,
  onRunAnalysis,
  isAnalyzing,
  onNavigateToImaging,
  isDemoLoaded,
}) => {
  const [activeStep, setActiveStep] = useState<number>(1);
  const [analysisMode, setAnalysisMode] = useState<'agentic' | 'baseline'>('agentic');
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Helper updates
  const updateField = (field: keyof PatientCase, value: any) => {
    onChangeCase({ ...currentCase, [field]: value });
  };

  const toggleSymptomTag = (tag: string) => {
    const existing = currentCase.symptoms || [];
    if (existing.includes(tag)) {
      updateField(
        'symptoms',
        existing.filter((s) => s !== tag)
      );
    } else {
      updateField('symptoms', [...existing, tag]);
    }
  };

  const addLab = (template: Omit<LabResult, 'value' | 'is_abnormal'>) => {
    const existing = currentCase.labs || [];
    if (!existing.some((l) => l.name === template.name)) {
      updateField('labs', [
        ...existing,
        {
          name: template.name,
          value: 0,
          unit: template.unit,
          reference_range: template.reference_range,
          is_abnormal: false,
        },
      ]);
    }
  };

  const removeLab = (index: number) => {
    const existing = [...(currentCase.labs || [])];
    existing.splice(index, 1);
    updateField('labs', existing);
  };

  const updateLab = (index: number, field: keyof LabResult, val: any) => {
    const existing = [...(currentCase.labs || [])];
    existing[index] = { ...existing[index], [field]: val };
    updateField('labs', existing);
  };

  const addMedication = () => {
    const meds = [...(currentCase.medications || [])];
    meds.push({ name: '', dosage: '', frequency: '' });
    updateField('medications', meds);
  };

  const updateMedication = (index: number, field: keyof Medication, val: string) => {
    const meds = [...(currentCase.medications || [])];
    meds[index] = { ...meds[index], [field]: val };
    updateField('medications', meds);
  };

  const removeMedication = (index: number) => {
    const meds = [...(currentCase.medications || [])];
    meds.splice(index, 1);
    updateField('medications', meds);
  };

  // Draft persistence using /api/cases
  const handleSaveDraft = async () => {
    setIsSaving(true);
    setSaveSuccess(null);
    setSaveError(null);
    try {
      const res = await api.createCase(currentCase);
      if (res.success) {
        setSaveSuccess(`Case draft persisted to database with Case ID: ${res.case_id}`);
        updateField('case_id', res.case_id);
      }
    } catch (err: any) {
      setSaveError(err.message || 'Failed to save case draft');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Stepper Navigation Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-3 shadow-xs">
        <div className="flex items-center gap-1 overflow-x-auto pb-1 scrollbar-thin">
          {SECTIONS.map((sec) => {
            const Icon = sec.icon;
            const isCurrent = activeStep === sec.id;
            const isCompleted = activeStep > sec.id;

            return (
              <button
                key={sec.id}
                onClick={() => setActiveStep(sec.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap transition-all shrink-0 ${
                  isCurrent
                    ? 'bg-teal-700 text-white shadow-xs'
                    : isCompleted
                    ? 'bg-slate-100 text-slate-800 hover:bg-slate-200'
                    : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
                }`}
              >
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-bold ${
                    isCurrent
                      ? 'bg-teal-800 text-teal-100'
                      : isCompleted
                      ? 'bg-teal-100 text-teal-800'
                      : 'bg-slate-200 text-slate-600'
                  }`}
                >
                  {isCompleted ? '✓' : sec.id}
                </span>
                <span>{sec.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Persistence Feedback */}
      {saveSuccess && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs px-4 py-2.5 rounded-lg flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            {saveSuccess}
          </span>
          <button onClick={() => setSaveSuccess(null)} className="text-emerald-700 font-bold">
            ×
          </button>
        </div>
      )}
      {saveError && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs px-4 py-2.5 rounded-lg flex items-center justify-between">
          <span className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600" />
            {saveError}
          </span>
          <button onClick={() => setSaveError(null)} className="text-rose-700 font-bold">
            ×
          </button>
        </div>
      )}

      {/* SECTION 1: Patient Demographics */}
      {activeStep === 1 && (
        <Card
          title="Section 1: Patient Demographics"
          subtitle="Essential patient identifiers for clinical case tracking"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <Input
              label="Patient Identifier (MRN / ID)"
              value={currentCase.patient_id || ''}
              onChange={(e) => updateField('patient_id', e.target.value)}
              placeholder="e.g. PT-10492"
              helperText="De-identified or institutional identifier"
              required
            />
            <Input
              label="Age (Years)"
              type="number"
              min={0}
              max={150}
              value={currentCase.age ?? ''}
              onChange={(e) => updateField('age', e.target.value ? parseInt(e.target.value) : null)}
              placeholder="e.g. 45"
              suffix="years"
              required
            />
            <Select
              label="Biological Sex"
              value={currentCase.sex || 'Unknown'}
              onChange={(e) => updateField('sex', e.target.value as Sex)}
              options={[
                { value: 'Unknown', label: 'Unspecified / Unknown' },
                { value: 'M', label: 'Male (M)' },
                { value: 'F', label: 'Female (F)' },
                { value: 'Other', label: 'Other' },
              ]}
            />
          </div>
        </Card>
      )}

      {/* SECTION 2: Presenting Complaints */}
      {activeStep === 2 && (
        <Card
          title="Section 2: Presenting Complaints"
          subtitle="Acute symptoms leading to clinical presentation"
        >
          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-700 mb-2 block">
                Quick Clinical Symptom Select:
              </label>
              <div className="flex flex-wrap gap-2">
                {COMMON_SYMPTOM_TAGS.map((tag) => {
                  const isSelected = (currentCase.symptoms || []).includes(tag);
                  return (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => toggleSymptomTag(tag)}
                      className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-all ${
                        isSelected
                          ? 'bg-teal-700 text-white border-teal-700 shadow-xs'
                          : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      {isSelected ? '✓ ' : '+ '}
                      {tag}
                    </button>
                  );
                })}
              </div>
            </div>

            <Textarea
              label="Full Symptoms Summary (comma-separated or descriptive)"
              value={(currentCase.symptoms || []).join(', ')}
              onChange={(e) =>
                updateField(
                  'symptoms',
                  e.target.value.split(',').map((s) => s.trim()).filter(Boolean)
                )
              }
              placeholder="e.g. fever, productive cough, shortness of breath, pleuritic chest pain"
              rows={3}
              helperText="Separate multiple symptoms with commas"
              required
            />
          </div>
        </Card>
      )}

      {/* SECTION 3: Medical History */}
      {activeStep === 3 && (
        <Card
          title="Section 3: Past Medical History & Comorbidities"
          subtitle="Chronic illnesses, prior admissions, and surgical history"
        >
          <Textarea
            label="Past Medical History & Comorbidities"
            value={(currentCase.history || []).join(', ')}
            onChange={(e) =>
              updateField(
                'history',
                e.target.value.split(',').map((h) => h.trim()).filter(Boolean)
              )
            }
            placeholder="e.g. hypertension, type 2 diabetes mellitus, chronic obstructive pulmonary disease, asthma"
            rows={4}
            helperText="Provide comma-separated list of confirmed comorbidities"
          />
        </Card>
      )}

      {/* SECTION 4: Current Medications */}
      {activeStep === 4 && (
        <Card
          title="Section 4: Current Medications"
          subtitle="Outpatient pharmacotherapy and dosages"
          action={
            <Button size="sm" variant="outline" leftIcon={<Plus className="w-3.5 h-3.5" />} onClick={addMedication}>
              Add Medication
            </Button>
          }
        >
          {(!currentCase.medications || currentCase.medications.length === 0) ? (
            <div className="p-8 text-center text-xs text-slate-400 bg-slate-50 rounded-lg border border-dashed border-slate-200">
              No current medications entered. Click "Add Medication" or proceed if patient takes no regular medications.
            </div>
          ) : (
            <div className="space-y-3">
              {currentCase.medications.map((med, idx) => (
                <div key={idx} className="flex items-center gap-3 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                  <Input
                    placeholder="Medication name (e.g. Metformin)"
                    value={med.name}
                    onChange={(e) => updateMedication(idx, 'name', e.target.value)}
                    containerClassName="flex-1"
                  />
                  <Input
                    placeholder="Dosage (e.g. 500mg)"
                    value={med.dosage}
                    onChange={(e) => updateMedication(idx, 'dosage', e.target.value)}
                    containerClassName="w-36"
                  />
                  <Input
                    placeholder="Frequency (e.g. BID / Daily)"
                    value={med.frequency}
                    onChange={(e) => updateMedication(idx, 'frequency', e.target.value)}
                    containerClassName="w-40"
                  />
                  <button
                    onClick={() => removeMedication(idx)}
                    className="p-2 text-slate-400 hover:text-rose-600 transition-colors"
                    title="Remove medication"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* SECTION 5: Allergies */}
      {activeStep === 5 && (
        <Card
          title="Section 5: Known Drug Allergies & Adverse Reactions"
          subtitle="Documented hypersensitivities and intolerance"
        >
          <Textarea
            label="Allergies (comma-separated)"
            value={(currentCase.allergies || []).join(', ')}
            onChange={(e) =>
              updateField(
                'allergies',
                e.target.value.split(',').map((a) => a.trim()).filter(Boolean)
              )
            }
            placeholder="e.g. Penicillin (rash), Sulfa drugs (anaphylaxis)"
            rows={3}
            helperText="State 'No Known Drug Allergies' (NKDA) if none identified"
          />
        </Card>
      )}

      {/* SECTION 6: Vital Signs */}
      {activeStep === 6 && (
        <Card
          title="Section 6: Admission / Current Vital Signs"
          subtitle="Physiological baseline parameters"
        >
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            <Input
              label="Heart Rate"
              type="number"
              value={currentCase.vitals?.heartRate ?? ''}
              onChange={(e) =>
                updateField('vitals', {
                  ...currentCase.vitals,
                  heartRate: e.target.value ? parseInt(e.target.value) : undefined,
                })
              }
              placeholder="e.g. 104"
              suffix="bpm"
            />
            <Input
              label="Systolic BP"
              type="number"
              value={currentCase.vitals?.bloodPressureSys ?? ''}
              onChange={(e) =>
                updateField('vitals', {
                  ...currentCase.vitals,
                  bloodPressureSys: e.target.value ? parseInt(e.target.value) : undefined,
                })
              }
              placeholder="e.g. 135"
              suffix="mmHg"
            />
            <Input
              label="Diastolic BP"
              type="number"
              value={currentCase.vitals?.bloodPressureDia ?? ''}
              onChange={(e) =>
                updateField('vitals', {
                  ...currentCase.vitals,
                  bloodPressureDia: e.target.value ? parseInt(e.target.value) : undefined,
                })
              }
              placeholder="e.g. 85"
              suffix="mmHg"
            />
            <Input
              label="Resp. Rate"
              type="number"
              value={currentCase.vitals?.respiratoryRate ?? ''}
              onChange={(e) =>
                updateField('vitals', {
                  ...currentCase.vitals,
                  respiratoryRate: e.target.value ? parseInt(e.target.value) : undefined,
                })
              }
              placeholder="e.g. 22"
              suffix="/min"
            />
            <Input
              label="SpO2"
              type="number"
              value={currentCase.vitals?.oxygenSaturation ?? ''}
              onChange={(e) =>
                updateField('vitals', {
                  ...currentCase.vitals,
                  oxygenSaturation: e.target.value ? parseFloat(e.target.value) : undefined,
                })
              }
              placeholder="e.g. 94"
              suffix="%"
            />
            <Input
              label="Temperature"
              type="number"
              step="0.1"
              value={currentCase.vitals?.temperature ?? ''}
              onChange={(e) =>
                updateField('vitals', {
                  ...currentCase.vitals,
                  temperature: e.target.value ? parseFloat(e.target.value) : undefined,
                })
              }
              placeholder="e.g. 38.9"
              suffix="°C"
            />
          </div>
        </Card>
      )}

      {/* SECTION 7: Laboratory Results */}
      {activeStep === 7 && (
        <Card
          title="Section 7: Laboratory Test Findings"
          subtitle="Hematology, biochemistry, and inflammatory markers"
          action={
            <Button
              size="sm"
              variant="outline"
              leftIcon={<Plus className="w-3.5 h-3.5" />}
              onClick={() => {
                const labs = [...(currentCase.labs || [])];
                labs.push({ name: '', value: 0, unit: '', reference_range: '', is_abnormal: false });
                updateField('labs', labs);
              }}
            >
              Add Custom Test
            </Button>
          }
        >
          {/* Quick Add Common Lab Panels */}
          <div className="mb-4">
            <label className="text-xs font-semibold text-slate-700 mb-2 block">
              Quick Add Standard Clinical Tests:
            </label>
            <div className="flex flex-wrap gap-2">
              {COMMON_LAB_TEMPLATES.map((tmpl) => (
                <button
                  key={tmpl.name}
                  type="button"
                  onClick={() => addLab(tmpl)}
                  className="text-xs px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium transition-colors border border-slate-200"
                >
                  + {tmpl.name}
                </button>
              ))}
            </div>
          </div>

          {/* Labs Table */}
          {(!currentCase.labs || currentCase.labs.length === 0) ? (
            <div className="p-8 text-center text-xs text-slate-400 bg-slate-50 rounded-lg border border-dashed border-slate-200">
              No lab values currently attached. Use the quick buttons above or add a custom test.
            </div>
          ) : (
            <div className="overflow-x-auto border border-slate-200 rounded-lg">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-2.5 font-semibold">Test Name</th>
                    <th className="px-4 py-2.5 font-semibold">Result Value</th>
                    <th className="px-4 py-2.5 font-semibold">Unit</th>
                    <th className="px-4 py-2.5 font-semibold">Reference Range</th>
                    <th className="px-4 py-2.5 font-semibold">Flag Outside Range</th>
                    <th className="px-4 py-2.5 font-semibold text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {currentCase.labs.map((lab, idx) => (
                    <tr key={idx} className={lab.is_abnormal ? 'bg-amber-50/40' : undefined}>
                      <td className="px-4 py-2">
                        <input
                          className="w-full bg-transparent font-medium text-slate-900 border-b border-transparent focus:border-teal-500 focus:outline-none"
                          value={lab.name}
                          onChange={(e) => updateLab(idx, 'name', e.target.value)}
                          placeholder="Test name"
                        />
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          step="0.01"
                          className="w-24 bg-white border border-slate-300 rounded px-2 py-1 text-slate-900 font-mono text-xs focus:outline-none focus:border-teal-600"
                          value={lab.value}
                          onChange={(e) => updateLab(idx, 'value', parseFloat(e.target.value) || 0)}
                        />
                      </td>
                      <td className="px-4 py-2">
                        <input
                          className="w-20 bg-transparent text-slate-600 border-b border-transparent focus:border-teal-500 focus:outline-none font-mono"
                          value={lab.unit}
                          onChange={(e) => updateLab(idx, 'unit', e.target.value)}
                          placeholder="e.g. mg/dL"
                        />
                      </td>
                      <td className="px-4 py-2">
                        <input
                          className="w-28 bg-transparent text-slate-500 border-b border-transparent focus:border-teal-500 focus:outline-none font-mono text-[11px]"
                          value={lab.reference_range}
                          onChange={(e) => updateLab(idx, 'reference_range', e.target.value)}
                          placeholder="e.g. 70-100"
                        />
                      </td>
                      <td className="px-4 py-2">
                        <label className="inline-flex items-center gap-1.5 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={Boolean(lab.is_abnormal)}
                            onChange={(e) => updateLab(idx, 'is_abnormal', e.target.checked)}
                            className="rounded text-teal-600 focus:ring-teal-500 h-4 w-4"
                          />
                          <span className={`text-[11px] font-medium ${lab.is_abnormal ? 'text-amber-700 font-bold' : 'text-slate-500'}`}>
                            {lab.is_abnormal ? 'Abnormal Flag' : 'Normal'}
                          </span>
                        </label>
                      </td>
                      <td className="px-4 py-2 text-right">
                        <button
                          onClick={() => removeLab(idx)}
                          className="text-slate-400 hover:text-rose-600 p-1 rounded"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* SECTION 8: Clinical Notes & Exam */}
      {activeStep === 8 && (
        <Card
          title="Section 8: Clinical Notes & Physical Examination"
          subtitle="Detailed clinician observations, auscultation, and presentation history"
        >
          <Textarea
            label="Detailed Examination Narrative"
            value={currentCase.clinical_notes || ''}
            onChange={(e) => updateField('clinical_notes', e.target.value)}
            placeholder="Document patient onset timeline, auscultatory crackles or wheezes, heart murmurs, abdominal palpation, and relevant clinical impressions..."
            rows={6}
            helperText="Provides critical context for General Physician and Specialist agents"
            required
          />
        </Card>
      )}

      {/* SECTION 9: Medical Imaging Attachment */}
      {activeStep === 9 && (
        <Card
          title="Section 9: Medical Imaging Attachment"
          subtitle="Chest radiographs or cross-sectional imaging for vision analysis"
          action={
            <Button size="sm" variant="outline" onClick={onNavigateToImaging}>
              Open Radiology Console
            </Button>
          }
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
            <div className="space-y-3">
              <p className="text-xs text-slate-600 leading-relaxed">
                Chest radiograph findings can be attached directly to this patient case. The LangGraph <strong>Radiology Agent</strong> will process findings using vision analysis or use calibrated fallback heuristics if vision is disabled.
              </p>
              {currentCase.image_path ? (
                <div className="p-3 bg-teal-50 border border-teal-200 rounded-lg flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ImageIcon className="w-5 h-5 text-teal-700" />
                    <div>
                      <p className="text-xs font-semibold text-teal-900">
                        {currentCase.image_path.split(/[/\\]/).pop()}
                      </p>
                      <p className="text-[11px] text-teal-700">Attached for multi-agent correlation</p>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => updateField('image_path', null)}
                    className="text-slate-500 hover:text-rose-600"
                  >
                    Detach
                  </Button>
                </div>
              ) : (
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-500 space-y-2">
                  <p>No radiography currently attached.</p>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={onNavigateToImaging}
                    leftIcon={<ImageIcon className="w-3.5 h-3.5" />}
                  >
                    Upload or Select Image in Imaging Workspace
                  </Button>
                </div>
              )}
            </div>

            <div className="border border-slate-200 rounded-xl p-4 bg-slate-50 flex flex-col items-center justify-center min-h-48 text-center">
              {currentCase.image_path ? (
                <img
                  src={`/${currentCase.image_path.replace(/^\.?\/?/, '')}`}
                  alt="Attached radiograph preview"
                  className="max-h-44 object-contain rounded border border-slate-300 shadow-xs"
                  onError={(e) => {
                    // Fallback preview
                    (e.target as HTMLElement).style.display = 'none';
                  }}
                />
              ) : (
                <div className="text-slate-400 space-y-1">
                  <ImageIcon className="w-8 h-8 mx-auto" />
                  <p className="text-xs font-medium">No image preview available</p>
                </div>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* SECTION 10: Review & Submit */}
      {activeStep === 10 && (
        <div className="space-y-6">
          <Card
            title="Section 10: Review Case & Execute Analysis"
            subtitle="Verify clinical parameters before orchestrating multi-agent diagnostic copilot"
            action={
              <Button
                size="sm"
                variant="outline"
                leftIcon={<Save className="w-3.5 h-3.5" />}
                onClick={handleSaveDraft}
                isLoading={isSaving}
              >
                Save Case Draft
              </Button>
            }
          >
            {/* Case Summary Review Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                <span className="text-slate-400 block uppercase tracking-wider text-[10px] font-semibold">
                  Patient Identity
                </span>
                <p className="text-sm font-bold text-slate-800 font-mono mt-1">
                  {currentCase.patient_id || 'PT-NOT-ASSIGNED'}
                </p>
                <p className="text-slate-600 mt-0.5">
                  Age: {currentCase.age ? `${currentCase.age}y` : 'N/A'}, Sex: {currentCase.sex || 'Unknown'}
                </p>
                {isDemoLoaded && (
                  <Badge variant="warning" className="mt-2">
                    Synthetic Educational Case
                  </Badge>
                )}
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                <span className="text-slate-400 block uppercase tracking-wider text-[10px] font-semibold">
                  Symptoms & History
                </span>
                <p className="text-slate-800 font-medium mt-1 truncate">
                  Symptoms: {(currentCase.symptoms || []).join(', ') || 'None entered'}
                </p>
                <p className="text-slate-600 mt-0.5 truncate">
                  History: {(currentCase.history || []).join(', ') || 'None entered'}
                </p>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                <span className="text-slate-400 block uppercase tracking-wider text-[10px] font-semibold">
                  Diagnostics & Imaging
                </span>
                <p className="text-slate-800 font-medium mt-1">
                  Labs: {currentCase.labs?.length || 0} tests recorded (
                  <span className="text-amber-700 font-bold">
                    {currentCase.labs?.filter((l) => l.is_abnormal).length || 0} abnormal
                  </span>
                  )
                </p>
                <p className="text-slate-600 mt-0.5">
                  Imaging: {currentCase.image_path ? 'Radiograph attached' : 'None'}
                </p>
              </div>
            </div>

            {/* Abnormal Labs Callout if any */}
            {currentCase.labs && currentCase.labs.some((l) => l.is_abnormal) && (
              <div className="mt-4 p-3 bg-amber-50/70 border border-amber-200 rounded-lg">
                <span className="text-xs font-semibold text-amber-900 block mb-1.5">
                  ⚠️ Abnormal Laboratory Flags:
                </span>
                <div className="flex flex-wrap gap-2 text-xs">
                  {currentCase.labs
                    .filter((l) => l.is_abnormal)
                    .map((l, i) => (
                      <span
                        key={i}
                        className="bg-white px-2.5 py-1 rounded border border-amber-300 font-mono text-amber-900"
                      >
                        <strong>{l.name}</strong>: {l.value} {l.unit} (Ref: {l.reference_range})
                      </span>
                    ))}
                </div>
              </div>
            )}

            {/* Engine Selection & Trigger */}
            <div className="mt-6 pt-5 border-t border-slate-200 space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1.5">
                  Select Diagnostic Protocol:
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <label
                    className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-all ${
                      analysisMode === 'agentic'
                        ? 'border-teal-600 bg-teal-50/60 ring-1 ring-teal-600'
                        : 'border-slate-200 bg-white hover:bg-slate-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name="analysisMode"
                      value="agentic"
                      checked={analysisMode === 'agentic'}
                      onChange={() => setAnalysisMode('agentic')}
                      className="mt-1 text-teal-600 focus:ring-teal-500"
                    />
                    <div>
                      <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                        Multi-Agent Clinical Debate (Recommended)
                      </span>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Stateful LangGraph coordination: GP ➔ Retrieval ➔ Radiologist ➔ Specialist ➔ Critic Verification (up to 3 debate iterations) ➔ Synthesizer.
                      </p>
                    </div>
                  </label>

                  <label
                    className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-all ${
                      analysisMode === 'baseline'
                        ? 'border-teal-600 bg-teal-50/60 ring-1 ring-teal-600'
                        : 'border-slate-200 bg-white hover:bg-slate-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name="analysisMode"
                      value="baseline"
                      checked={analysisMode === 'baseline'}
                      onChange={() => setAnalysisMode('baseline')}
                      className="mt-1 text-teal-600 focus:ring-teal-500"
                    />
                    <div>
                      <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                        Single-Shot Baseline RAG
                      </span>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Fast single-pass hybrid retrieval and prompt generation without multi-agent verification loop.
                      </p>
                    </div>
                  </label>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
                <span className="text-xs text-slate-500">
                  ⚠️ Output intended for clinical decision support and physician review only.
                </span>

                <Button
                  size="lg"
                  variant="primary"
                  isLoading={isAnalyzing}
                  leftIcon={<Sparkles className="w-5 h-5" />}
                  onClick={() => onRunAnalysis(analysisMode)}
                  className="w-full sm:w-auto shadow-md"
                >
                  {isAnalyzing
                    ? 'Orchestrating Multi-Agent Diagnostic Workflow...'
                    : 'Execute Multi-Agent Clinical Analysis'}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Stepper Footer Controls */}
      <div className="flex items-center justify-between pt-2">
        <Button
          variant="outline"
          size="sm"
          disabled={activeStep === 1}
          leftIcon={<ArrowLeft className="w-4 h-4" />}
          onClick={() => setActiveStep((prev) => Math.max(1, prev - 1))}
        >
          Previous Section
        </Button>

        <span className="text-xs font-medium text-slate-500">
          Section {activeStep} of {SECTIONS.length}: {SECTIONS[activeStep - 1].label}
        </span>

        {activeStep < 10 ? (
          <Button
            variant="primary"
            size="sm"
            rightIcon={<ArrowRight className="w-4 h-4" />}
            onClick={() => setActiveStep((prev) => Math.min(10, prev + 1))}
          >
            Next Section
          </Button>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={handleSaveDraft}
            isLoading={isSaving}
            leftIcon={<Save className="w-3.5 h-3.5" />}
          >
            Save Draft
          </Button>
        )}
      </div>
    </div>
  );
};
