import { LabResult, PatientCase } from '../types/clinical';

export const COMMON_LAB_TEMPLATES: Array<Omit<LabResult, 'value' | 'is_abnormal'>> = [
  { name: 'Hemoglobin', unit: 'g/dL', reference_range: '12.0-17.5' },
  { name: 'WBC', unit: '×10³/μL', reference_range: '4.5-11.0' },
  { name: 'Platelets', unit: '×10³/μL', reference_range: '150-400' },
  { name: 'Glucose', unit: 'mg/dL', reference_range: '70-100' },
  { name: 'Creatinine', unit: 'mg/dL', reference_range: '0.6-1.3' },
  { name: 'CRP', unit: 'mg/L', reference_range: '<10' },
  { name: 'Troponin', unit: 'ng/mL', reference_range: '<0.04' },
  { name: 'Blood Urea Nitrogen', unit: 'mg/dL', reference_range: '7-20' },
  { name: 'Sodium', unit: 'mEq/L', reference_range: '135-145' },
  { name: 'Potassium', unit: 'mEq/L', reference_range: '3.5-5.0' },
];

export const DEMO_CASE: PatientCase = {
  case_id: 'DEMO-CASE-2026',
  patient_id: 'PT-10492-DEMO',
  age: 45,
  sex: 'M',
  symptoms: ['fever', 'productive cough', 'shortness of breath', 'fatigue'],
  history: ['hypertension', 'type 2 diabetes'],
  medications: [
    { name: 'Metformin', dosage: '500mg', frequency: 'twice daily' },
    { name: 'Lisinopril', dosage: '10mg', frequency: 'once daily' },
  ],
  allergies: ['Penicillin (mild cutaneous rash)'],
  vitals: {
    heartRate: 104,
    bloodPressureSys: 135,
    bloodPressureDia: 85,
    respiratoryRate: 22,
    oxygenSaturation: 94,
    temperature: 38.9,
  },
  clinical_notes:
    'Patient presents with a 3-day history of acute productive cough with purulent yellowish sputum, tactile fevers up to 38.9°C, and progressive dyspnea on mild exertion. Physical examination reveals inspiratory crackles localized over the right lower hemithorax. Heart sounds regular without murmurs. Mild pleuritic discomfort noted during deep inspiration.',
  case_description: 'Suspected Community-Acquired Pneumonia with secondary cardiopulmonary risk factors.',
  labs: [
    { name: 'WBC', value: 14.5, unit: '×10³/μL', reference_range: '4.5-11.0', is_abnormal: true },
    { name: 'CRP', value: 85.0, unit: 'mg/L', reference_range: '<10', is_abnormal: true },
    { name: 'Hemoglobin', value: 13.2, unit: 'g/dL', reference_range: '12.0-17.5', is_abnormal: false },
    { name: 'Glucose', value: 145.0, unit: 'mg/dL', reference_range: '70-100', is_abnormal: true },
    { name: 'Creatinine', value: 1.1, unit: 'mg/dL', reference_range: '0.6-1.3', is_abnormal: false },
    { name: 'Platelets', value: 245, unit: '×10³/μL', reference_range: '150-400', is_abnormal: false },
  ],
  image_path: 'data/demo/demo_chest_xray.png',
};
