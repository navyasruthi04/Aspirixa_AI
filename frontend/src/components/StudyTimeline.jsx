import { Check, Clock } from 'lucide-react';
import Badge from './Badge.jsx';

const statusUI = { completed: ['Completed', 'green'], current: ['Current', 'primary'], upcoming: ['Upcoming', 'gray'] };

export default function StudyTimeline({ items, onToggle, compact = false }) {
  return (
    <ol className={`tl ${compact ? 'tl-c' : ''}`}>
      {(items || []).map((it, index) => {
        const [label, tone] = statusUI[it.status] || statusUI.upcoming;
        return (
          <li key={it.id ?? `${it.subject}-${it.topic}-${index}`} className={`tl-item s-${it.status}`}>
            <div className="tl-time"><b>{it.time}</b><small>{it.period}</small></div>
            <span className="tl-dot">{it.status === 'completed' && <Check size={11} aria-hidden="true" />}</span>
            <div className="tl-card">
              <div><strong>{it.subject}</strong><span className="muted"> &middot; {it.topic}</span></div>
              <div className="tl-meta">
                <span className="t"><Clock size={13} aria-hidden="true" /> {it.minutes} min</span>
                {it.weak && <Badge tone="amber">Weak Topic</Badge>}
                {it.extra && <Badge tone="blue">Added by you</Badge>}
                <Badge tone={tone}>{label}</Badge>
              </div>
              {onToggle && (
                <button className="link-btn" style={{ marginTop: 6 }} onClick={() => onToggle(it.id)}>
                  {it.status === 'completed' ? 'Mark as pending' : 'Mark as complete'}
                </button>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}