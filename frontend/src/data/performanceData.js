// Sample analytics for the frontend demo. The backend will replace these.
export const analytics = {
  summary: [
    { id: 'acc', label: 'Overall Accuracy', value: '76', unit: '%', trend: '+8% this week', tone: 'green' },
    { id: 'mastery', label: 'Mastery', value: '68', unit: '%', trend: '+4% this week', tone: 'primary' },
    { id: 'solved', label: 'Questions Solved', value: '248', unit: '', trend: '+36 this week', tone: 'blue' },
    { id: 'hours', label: 'Study Hours', value: '14.5', unit: ' hrs', trend: '+1.5 hrs vs last week', tone: 'amber' },
  ],
  weekly: { labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], values: [68, 70, 72, 71, 74, 75, 76] },
  subjects: [
    { name: 'Quantitative Aptitude', short: 'Quant', value: 72 },
    { name: 'Reasoning', short: 'Reasoning', value: 81 },
    { name: 'English', short: 'English', value: 67 },
    { name: 'General Awareness', short: 'GA', value: 45 },
  ],
  studyTime: { labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], values: [1.5, 2, 2.5, 1, 3, 2.5, 2] },
  difficulty: [
    { label: 'Easy', value: 82, color: '#20A779' },
    { label: 'Moderate', value: 118, color: '#5B4FE9' },
    { label: 'Difficult', value: 48, color: '#D69E2E' },
  ],
  topics: [
    { name: 'Coding-Decoding', subject: 'Reasoning', value: 81 },
    { name: 'Percentages', subject: 'Quantitative Aptitude', value: 58 },
    { name: 'Error Spotting', subject: 'English', value: 56 },
    { name: 'Current Affairs', subject: 'General Awareness', value: 44 },
  ],
  insights: [
    'Your reasoning accuracy has improved over the last 7 days.',
    'General Awareness remains your lowest mastery area.',
    'Short revision sessions may help maintain completed topics.',
  ],
};