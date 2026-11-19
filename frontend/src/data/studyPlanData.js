export const schedule = [
  { id: 's1', time: '09:00', period: 'AM', subject: 'Quantitative Aptitude', topic: 'Percentages', minutes: 60, weak: true, status: 'completed' },
  { id: 's2', time: '11:00', period: 'AM', subject: 'Reasoning', topic: 'Coding-Decoding', minutes: 45, weak: false, status: 'current' },
  { id: 's3', time: '06:30', period: 'PM', subject: 'English', topic: 'Error Spotting', minutes: 45, weak: true, status: 'upcoming' },
  { id: 's4', time: '08:00', period: 'PM', subject: 'Revision', topic: 'Current Affairs + Revision', minutes: 30, weak: false, status: 'upcoming' },
];

export const planSummary = { dailyHours: 3, weakTopics: 4, weeklyGoal: 18, weeklyDone: 14.5, consistency: 81 };

export const whyPlan = [
  { title: 'Weak topics receive additional practice', text: 'Percentages and Error Spotting get longer sessions.' },
  { title: 'Available study hours are respected', text: 'Your day is planned inside your 3 hours.' },
  { title: 'Revision is automatically included', text: 'A short revision slot is added every day.' },
  { title: 'Subjects remain balanced', text: 'No subject is ignored while you fix weak ones.' },
  { title: 'Completed topics are revisited', text: 'Finished topics return later so they stay fresh.' },
];

export const planFlow = ['Weak topics', 'Available time', 'Syllabus', 'Time allocation', 'Daily plan'];