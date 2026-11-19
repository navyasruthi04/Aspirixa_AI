export default function Button({ variant = 'primary', size = 'md', icon: Icon, iconRight: IconRight, className = '', children, ...rest }) {
  return (
    <button type="button" className={`btn btn-${variant} btn-${size} ${className}`} {...rest}>
      {Icon && <Icon size={16} aria-hidden="true" />}
      {children}
      {IconRight && <IconRight size={16} aria-hidden="true" />}
    </button>
  );
}