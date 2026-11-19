export default function Logo({ size = 36, showText = true }) {
  return (
    <div className="logo">
      <svg width={size} height={size} viewBox="0 0 40 40" role="img" aria-label="Aspirixa AI logo">
        <defs>
          <linearGradient id="logoG" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#7568FF" />
            <stop offset="1" stopColor="#4F8DF7" />
          </linearGradient>
        </defs>
        <rect width="40" height="40" rx="11" fill="url(#logoG)" />
        <path d="M9 29 L16 21 L22 25 L30 13" fill="none" stroke="#fff" strokeOpacity=".75" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="9" cy="29" r="2.2" fill="#fff" />
        <circle cx="16" cy="21" r="2.2" fill="#fff" />
        <circle cx="22" cy="25" r="2.2" fill="#fff" />
        <path d="M30 6.5 L31.7 10.3 L35.5 12 L31.7 13.7 L30 17.5 L28.3 13.7 L24.5 12 L28.3 10.3 Z" fill="#fff" />
      </svg>
      {showText && (
        <div className="logo-text">
          <strong>ASPIRIXA<span> AI</span></strong>
          <small>Your Exam. Your Path.</small>
        </div>
      )}
    </div>
  );
}