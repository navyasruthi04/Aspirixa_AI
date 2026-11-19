import { useEffect, useState } from 'react';
import { Sparkles, CheckCircle2 } from 'lucide-react';
import Card from './Card.jsx';
import Badge from './Badge.jsx';
import ProgressBar from './ProgressBar.jsx';

const R = 40;
const C = 2 * Math.PI * R;

export function ScoreRing({ value, size = 96, label = 'Suitability' }) {
  const [offset, setOffset] = useState(C);
  useEffect(() => {
    const id = requestAnimationFrame(() => setOffset(C * (1 - value / 100)));
    return () => cancelAnimationFrame(id);
  }, [value]);
  return (
    <div className="ring" style={{ width: size, height: size }} role="img" aria-label={`${label} ${value} percent`}>
      <svg viewBox="0 0 100 100">
        <defs>
          <linearGradient id="ringG" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#7568FF" /><stop offset="1" stopColor="#4F8DF7" />
          </linearGradient>
        </defs>
        <circle cx="50" cy="50" r={R} className="ring-bg" />
        <circle cx="50" cy="50" r={R} className="ring-fg" strokeDasharray={C} strokeDashoffset={offset} transform="rotate(-90 50 50)" />
      </svg>
      <div className="ring-c"><strong>{value}%</strong><small>{label}</small></div>
    </div>
  );
}

export const factorLabels = {
  qualification: 'Qualification Match',
  subject: 'Subject Alignment',
  time: 'Study Time',
  level: 'Preparation Level',
};

export default function RecommendationCard({ rec, action }) {
  return (
    <Card className="rec-card">
      <div className="rec-top">
        <div>
          <span className="eyebrow"><Sparkles size={14} aria-hidden="true" /> AI Recommendation</span>
          <h2>{rec.name}</h2>
          <p className="muted">Recommended exam &middot; {rec.body}</p>
          <div className="row mt8">
            <Badge tone="green" icon={CheckCircle2}>Eligible</Badge>
            <Badge tone="primary">Suitability {rec.suitability}%</Badge>
          </div>
        </div>
        <ScoreRing value={rec.suitability} />
      </div>
      <div className="why">
        <h4>Why this recommendation?</h4>
        <p>{rec.explanation}</p>
      </div>
      <div className="factor-grid">
        {Object.entries(factorLabels).map(([k, label]) => (
          <div className="factor" key={k}>
            <span>{label}</span>
            <strong>{rec.factors[k]}%</strong>
            <ProgressBar value={rec.factors[k]} size="sm" label={label} />
          </div>
        ))}
      </div>
      {action}
    </Card>
  );
}