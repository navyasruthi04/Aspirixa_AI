import { useEffect, useState } from 'react';

export default function ProgressBar({ value, tone = 'primary', text, label, showValue = false, size = 'md' }) {
  const [w, setW] = useState(0);
  useEffect(() => {
    const id = requestAnimationFrame(() => setW(value)); // starts at 0 so the bar animates
    return () => cancelAnimationFrame(id);
  }, [value]);

  return (
    <div className="pb-wrap">
      {(text || showValue) && (
        <div className="pb-top"><span>{text}</span>{showValue && <b>{value}%</b>}</div>
      )}
      <div className={`pb pb-${size}`} role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100} aria-label={label || text || 'Progress'}>
        <div className={`pb-fill t-${tone}`} style={{ width: `${w}%` }} />
      </div>
    </div>
  );
}