import { Link } from 'react-router-dom';
import { Check } from 'lucide-react';

const stages = [
  { n: '01', label: 'Profile', to: '/profile' },
  { n: '02', label: 'Recommend', to: '/exam-recommendation' },
  { n: '03', label: 'Diagnose', to: '/diagnostic' },
  { n: '04', label: 'Plan', to: '/study-plan' },
  { n: '05', label: 'Adapt', to: '/adaptive-quiz' },
  { n: '06', label: 'Improve', to: '/performance' },
];

// active = 1 to 6. Earlier stages show as done.
export default function AIJourney({ active = 1, compact = false, dark = false }) {
  return (
    <nav className={`journey ${compact ? 'compact' : ''} ${dark ? 'dark' : ''}`} aria-label="AI Journey">
      <ol>
        {stages.map((s, i) => {
          const state = i + 1 < active ? 'done' : i + 1 === active ? 'active' : 'todo';
          return (
            <li key={s.n} className={state}>
              <Link to={s.to} aria-current={state === 'active' ? 'step' : undefined}>
                <span className="j-dot">{state === 'done' ? <Check size={12} aria-hidden="true" /> : s.n}</span>
                <span>{s.label}</span>
              </Link>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}