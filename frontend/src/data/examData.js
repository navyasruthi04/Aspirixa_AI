export const exams = [
  { id: 'ssc-cgl', name: 'SSC CGL', body: 'Staff Selection Commission', status: 'eligible', graduateOnly: true, maxAge: 32,
    note: 'Graduate in any stream. Indicative age limit 18-32 (General).',
    base: { qualification: 92, subject: 89, time: 84, level: 83 } },
  { id: 'bank-po', name: 'Banking PO', body: 'IBPS / SBI', status: 'eligible', graduateOnly: true, maxAge: 30,
    note: 'Graduate in any stream. Indicative age limit 20-30 (General).',
    base: { qualification: 88, subject: 80, time: 82, level: 78 } },
  { id: 'rrb-ntpc', name: 'Railway NTPC', body: 'Railway Recruitment Boards', status: 'eligible', graduateOnly: false, maxAge: 33,
    note: 'Posts open at both 12th and graduate level. Indicative age limit 18-33.',
    base: { qualification: 84, subject: 76, time: 86, level: 74 } },
  { id: 'upsc', name: 'UPSC CSE', body: 'Union Public Service Commission', status: 'eligible', graduateOnly: true, maxAge: 32,
    note: 'Graduate in any stream. Indicative age limit 21-32 (General).',
    base: { qualification: 78, subject: 64, time: 52, level: 60 } },
  { id: 'cds', name: 'CDS', body: 'UPSC - Defence Services', status: 'check', graduateOnly: false, maxAge: 24,
    note: 'Requirements differ by academy (IMA, OTA, Navy, Air Force). Check the official notification.',
    base: { qualification: 70, subject: 55, time: 70, level: 62 } },
];

export const topExplanation =
  'Your qualification satisfies the eligibility criteria, your preferred subjects align with the exam syllabus, and your available study time matches the preparation requirement.';

// Sample values for the frontend demo. Real values will come from the SHAP module in the backend.
export const shapSample = [
  { label: 'Subject Preference', value: 0.31 },
  { label: 'Study Time', value: 0.24 },
  { label: 'Qualification', value: 0.19 },
  { label: 'Preparation Level', value: 0.15 },
  { label: 'Syllabus Breadth', value: -0.07 },
];

export const algorithms = [
  { name: 'Eligibility Rules', role: 'Filters exams you can apply for' },
  { name: 'XGBoost', role: 'Predicts suitability' },
  { name: 'TOPSIS', role: 'Ranks the options' },
  { name: 'SHAP', role: 'Explains the reasons' },
];