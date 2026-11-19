import ProgressBar from './ProgressBar.jsx';
import Badge from './Badge.jsx';
import { masteryStatus } from '../utils/helpers.js';

export default function MasteryBar({ label, sub, value }) {
  const s = masteryStatus(value);
  return (
    <div className="mastery">
      <div className="mastery-top">
        <div><strong>{label}</strong>{sub && <small>{sub}</small>}</div>
        <div className="row"><b>{value}%</b><Badge tone={s.tone}>{s.label}</Badge></div>
      </div>
      <ProgressBar value={value} tone={s.tone} size="sm" label={`${label} mastery`} />
    </div>
  );
}