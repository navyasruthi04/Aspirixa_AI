export const profileOptions = {
  qualifications: ['12th Pass', 'Diploma', 'B.Tech CSE', 'B.Tech / B.E. (Other)', 'B.Sc', 'B.Com', 'B.A.', 'Postgraduate'],
  levels: ['Beginner', 'Intermediate', 'Advanced'],
  hours: [1, 2, 3, 4, 5, 6],
  subjects: ['Quantitative Aptitude', 'Reasoning', 'English', 'General Awareness'],
  fields: ['Administration / General', 'Banking & Finance', 'Railways', 'Defence', 'Teaching'],
  exams: ['SSC CGL', 'UPSC', 'Banking PO', 'Railway NTPC', 'CDS'],
};

export const student = {
  fullName: 'Navya',
  qualification: 'B.Tech CSE',
  age: 21,
  targetExam: 'SSC CGL',
  level: 'Intermediate',
  dailyHours: 3,
  subjects: ['Quantitative Aptitude', 'Reasoning', 'English'],
  field: 'Administration / General',
  streak: 12,
  prefs: { dailyReminders: true, adaptiveDifficulty: true, weakTopicPriority: true, revisionReminders: false },
};

export const dashboardStats = [
  { id: 'progress', label: 'Overall Progress', value: '68', unit: '%', trend: '+5% this week', tone: 'primary' },
  { id: 'accuracy', label: 'Quiz Accuracy', value: '76', unit: '%', trend: '+8% this week', tone: 'green' },
  { id: 'streak', label: 'Study Streak', value: '12', unit: ' Days', trend: 'Your longest so far', tone: 'amber' },
  { id: 'time', label: 'Study Time', value: '14.5', unit: ' hrs', trend: '+1.5 hrs vs last week', tone: 'blue' },
  { id: 'solved', label: 'Questions Solved', value: '248', unit: '', trend: '+36 this week', tone: 'primary' },
];

export const achievements = [
  { id: 'a1', label: 'First Diagnostic', note: 'Completed', earned: true },
  { id: 'a2', label: '7-Day Streak', note: 'Completed', earned: true },
  { id: 'a3', label: '100 Questions', note: 'Completed', earned: true },
  { id: 'a4', label: 'Weak Topic Crusher', note: '2 of 4 topics', earned: false },
  { id: 'a5', label: 'Consistency Champion', note: '81 of 90%', earned: false },
];

export const leaderboard = {
  City: [
    { rank: 1, name: 'Karthik R.', xp: 2840 }, { rank: 2, name: 'Divya S.', xp: 2715 },
    { rank: 3, name: 'Navya (You)', xp: 2590, me: true }, { rank: 4, name: 'Arjun M.', xp: 2480 },
  ],
  State: [
    { rank: 1, name: 'Sneha V.', xp: 3320 }, { rank: 2, name: 'Rahul T.', xp: 3190 },
    { rank: 3, name: 'Priya N.', xp: 3050 }, { rank: 14, name: 'Navya (You)', xp: 2590, me: true },
  ],
  'All India': [
    { rank: 1, name: 'Aditya P.', xp: 4120 }, { rank: 2, name: 'Ishita G.', xp: 4005 },
    { rank: 3, name: 'Mohit S.', xp: 3980 }, { rank: 212, name: 'Navya (You)', xp: 2590, me: true },
  ],
};

export const notifications = [
  { id: 'n1', text: 'Reasoning session starts at 11:00 AM', time: 'Today' },
  { id: 'n2', text: 'Your weekly accuracy improved by 8%', time: 'Yesterday' },
  { id: 'n3', text: 'Revision due: Percentages', time: '2 days ago' },
];