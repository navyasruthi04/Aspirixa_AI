import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { X, Lightbulb } from 'lucide-react';
import Logo from './Logo.jsx';
import { navItems, bottomNav } from '../data/navData.js';
import { sidebarTips } from '../data/quotes.js';

export default function Sidebar({ open, onClose }) {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((v) => (v + 1) % sidebarTips.length), 9000);
    return () => clearInterval(t);
  }, []);

  return (
    <aside className={`sidebar ${open ? 'open' : ''}`} aria-label="Primary">
      <div className="sb-brand">
        <Logo />
        <button className="icon-btn sb-close" onClick={onClose} aria-label="Close menu"><X size={18} /></button>
      </div>
      <nav className="sb-nav">
        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end} title={label} className={({ isActive }) => `sb-link ${isActive ? 'active' : ''}`}>
            <Icon size={18} aria-hidden="true" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sb-tip">
        <div className="sb-tip-h"><Lightbulb size={14} aria-hidden="true" /> AI Preparation Tip</div>
        <p key={i}>&ldquo;{sidebarTips[i]}&rdquo;</p>
      </div>
    </aside>
  );
}

export function BottomNav() {
  return (
    <nav className="bottom-nav" aria-label="Quick navigation">
      {navItems.filter((n) => bottomNav.includes(n.to)).map(({ to, short, icon: Icon, end }) => (
        <NavLink key={to} to={to} end={end} className={({ isActive }) => `bn-link ${isActive ? 'active' : ''}`}>
          <Icon size={19} aria-hidden="true" />
          <span>{short}</span>
        </NavLink>
      ))}
    </nav>
  );
}