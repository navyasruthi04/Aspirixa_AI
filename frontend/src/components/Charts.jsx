// Small custom SVG charts, so no chart library is needed.

export function LineChart({ values, labels, min = 60, max = 80 }) {
  const W = 520, H = 200, P = { l: 36, r: 14, t: 14, b: 26 };
  const x = (i) => P.l + (i * (W - P.l - P.r)) / (values.length - 1);
  const y = (v) => P.t + (1 - (v - min) / (max - min)) * (H - P.t - P.b);
  const pts = values.map((v, i) => [x(i), y(v)]);
  const line = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0]},${p[1]}`).join(' ');
  const area = `${line} L${x(values.length - 1)},${H - P.b} L${x(0)},${H - P.b} Z`;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart" role="img" aria-label="Weekly accuracy line chart">
      <defs>
        <linearGradient id="areaG" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#5B4FE9" stopOpacity=".22" /><stop offset="1" stopColor="#5B4FE9" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[min, (min + max) / 2, max].map((t) => (
        <g key={t}>
          <line x1={P.l} x2={W - P.r} y1={y(t)} y2={y(t)} className="grid-l" />
          <text x={P.l - 8} y={y(t) + 4} textAnchor="end" className="ax">{t}%</text>
        </g>
      ))}
      <path d={area} fill="url(#areaG)" />
      <path d={line} className="line-p" />
      {pts.map((p, i) => (
        <g key={labels[i]}>
          <circle cx={p[0]} cy={p[1]} r="4" className="dot-p" />
          <text x={p[0]} y={H - 8} textAnchor="middle" className="ax">{labels[i]}</text>
        </g>
      ))}
    </svg>
  );
}

export function BarChart({ items, max = 100, unit = '%' }) {
  const W = 520, H = 200, P = { l: 36, r: 10, t: 18, b: 26 };
  const bw = (W - P.l - P.r) / items.length;
  const y = (v) => P.t + (1 - v / max) * (H - P.t - P.b);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart" role="img" aria-label="Bar chart">
      {[0, max / 2, max].map((t) => (
        <g key={t}>
          <line x1={P.l} x2={W - P.r} y1={y(t)} y2={y(t)} className="grid-l" />
          <text x={P.l - 8} y={y(t) + 4} textAnchor="end" className="ax">{t}{unit}</text>
        </g>
      ))}
      {items.map((it, i) => {
        const w = Math.min(46, bw * 0.55);
        const cx = P.l + bw * i + bw / 2;
        return (
          <g key={it.label}>
            <rect x={cx - w / 2} y={y(it.value)} width={w} height={H - P.b - y(it.value)} rx="6" className={`t-fill-${it.tone || 'primary'}`} />
            <text x={cx} y={y(it.value) - 6} textAnchor="middle" className="ax-b">{it.value}{unit}</text>
            <text x={cx} y={H - 8} textAnchor="middle" className="ax">{it.label}</text>
          </g>
        );
      })}
    </svg>
  );
}

export function DonutChart({ items }) {
  const total = items.reduce((a, b) => a + b.value, 0);
  const r = 42;
  const C = 2 * Math.PI * r;
  let offset = 0;
  return (
    <div className="donut">
      <svg viewBox="0 0 120 120" role="img" aria-label="Question difficulty distribution">
        <g transform="rotate(-90 60 60)">
          <circle cx="60" cy="60" r={r} className="donut-bg" />
          {items.map((it) => {
            const len = (it.value / total) * C;
            const el = (
              <circle key={it.label} cx="60" cy="60" r={r} fill="none" stroke={it.color} strokeWidth="14"
                strokeDasharray={`${len - 2} ${C - len + 2}`} strokeDashoffset={-offset} />
            );
            offset += len;
            return el;
          })}
        </g>
        <text x="60" y="58" textAnchor="middle" className="donut-n">{total}</text>
        <text x="60" y="73" textAnchor="middle" className="ax">questions</text>
      </svg>
      <ul className="legend">
        {items.map((it) => (
          <li key={it.label}><i style={{ background: it.color }} />{it.label}<b>{it.value}</b></li>
        ))}
      </ul>
    </div>
  );
}