export default function Badge({ tone = 'gray', icon: Icon, children }) {
  return (
    <span className={`badge b-${tone}`}>
      {Icon && <Icon size={12} aria-hidden="true" />}
      {children}
    </span>
  );
}