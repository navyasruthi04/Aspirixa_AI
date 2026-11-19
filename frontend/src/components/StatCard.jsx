export default function StatCard({ icon: Icon, label, value, unit, trend, tone = 'primary' }) {
  return (
    <div className="stat">
      <div className={`stat-ic t-soft-${tone}`}><Icon size={19} aria-hidden="true" /></div>
      <div>
        <span className="stat-l">{label}</span>
        <strong>{value}<small>{unit}</small></strong>
        {trend && <span className="stat-t">{trend}</span>}
      </div>
    </div>
  );
}