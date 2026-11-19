export const masteryStatus = (v) =>
  v >= 70 ? { label: 'Strong', tone: 'green' }
  : v >= 55 ? { label: 'Developing', tone: 'blue' }
  : { label: 'Needs Attention', tone: 'amber' };

// Frontend demo rule. The real value will come from the BKT backend.
export const difficultyFor = (m) => (m < 40 ? 'Easy' : m <= 60 ? 'Moderate' : 'Difficult');

export const diffTone = {
  Easy: 'green', Moderate: 'blue', Difficult: 'amber',
  Medium: 'blue', Hard: 'amber',
  Beginner: 'green', Intermediate: 'blue', Advanced: 'amber',
};

export const greeting = () => {
  const h = new Date().getHours();
  return h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
};