import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Menu, Search, Bell, Flame } from 'lucide-react';
import { navItems } from '../data/navData.js';
import { student, notifications } from '../data/studentData.js';

export default function Topbar({ onMenu }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const [q, setQ] = useState('');
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const current = navItems.find((n) => n.to === pathname) || navItems[0];

  useEffect(() => {
    const close = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  const submit = (e) => {
    e.preventDefault();
    navigate(`/resources?q=${encodeURIComponent(q)}`);
  };

  return (
    <header className="topbar">
      <button className="icon-btn menu-btn" onClick={onMenu} aria-label="Open menu"><Menu size={20} /></button>
      <div className="tb-title">
        <span className="tb-crumb">Aspirixa AI</span>
        <h2>{current.label}</h2>
      </div>
      <form className="tb-search" onSubmit={submit} role="search">
        <Search size={16} aria-hidden="true" />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search topics, notes, PYQs..." aria-label="Search resources" />
      </form>
      <div className="tb-right">
        <span className="streak-chip" title="Study streak"><Flame size={15} aria-hidden="true" /> {student.streak}</span>
        <div className="dd" ref={ref}>
          <button className="icon-btn" aria-label="Notifications" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
            <Bell size={18} /><i className="dot" />
          </button>
          {open && (
            <div className="dd-menu" role="menu">
              <h4>Notifications</h4>
              {notifications.map((n) => (
                <div className="dd-item" role="menuitem" key={n.id}>{n.text}<small>{n.time}</small></div>
              ))}
            </div>
          )}
        </div>
        <div className="avatar" aria-label="Signed in as Navya">{student.fullName[0]}</div>
      </div>
    </header>
  );
}