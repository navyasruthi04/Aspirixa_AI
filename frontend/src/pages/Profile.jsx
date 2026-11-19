import { useState } from 'react';
import { Pencil, Save, Bell, Zap, Target, RotateCcw, X } from 'lucide-react';
import { useAsync } from '../hooks/useAsync.js';
import { getStudentProfile, updateStudentProfile } from '../services/api.js';
import { profileOptions } from '../data/studentData.js';
import { quotes } from '../data/quotes.js';
import { useToast } from '../components/Toast.jsx';
import { AsyncView } from '../components/EmptyState.jsx';
import Card from '../components/Card.jsx';
import Button from '../components/Button.jsx';
import Badge from '../components/Badge.jsx';

const prefList = [
  { key: 'dailyReminders', title: 'Daily reminders', text: 'A gentle nudge at your study time', icon: Bell },
  { key: 'adaptiveDifficulty', title: 'Adaptive difficulty', text: 'Quiz difficulty follows your mastery', icon: Zap },
  { key: 'weakTopicPriority', title: 'Weak-topic priority', text: 'More time for topics that need attention', icon: Target },
  { key: 'revisionReminders', title: 'Revision reminders', text: 'Revisit completed topics on schedule', icon: RotateCcw },
];

function Switch({ checked, onChange, label }) {
  return (
    <button type="button" role="switch" aria-checked={checked} aria-label={label} className={`switch ${checked ? 'on' : ''}`} onClick={onChange}>
      <i />
    </button>
  );
}

function ProfileForm({ initial }) {
  const toast = useToast();
  const [saved, setSaved] = useState(initial);
  const [form, setForm] = useState(initial);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const toggleSubject = (s) => set('subjects', form.subjects.includes(s) ? form.subjects.filter((x) => x !== s) : [...form.subjects, s]);

  const save = async (e) => {
    e.preventDefault();
    if (!form.fullName.trim()) return toast.push('Please enter your name.', 'warning');
    if (form.age < 16 || form.age > 45) return toast.push('Enter an age between 16 and 45.', 'warning');
    if (!form.subjects.length) return toast.push('Select at least one preferred subject.', 'warning');
    setSaving(true);
    try {
      const r = await updateStudentProfile(form);
      setSaved(r); setForm(r); setEditing(false);
      toast.push('Profile saved successfully.');
    } catch {
      toast.push('Could not save your profile. Try again.', 'warning');
    } finally {
      setSaving(false);
    }
  };

  const cancel = () => { setForm(saved); setEditing(false); };

  const togglePref = async (key) => {
    const prefs = { ...form.prefs, [key]: !form.prefs[key] };
    set('prefs', prefs);
    setSaved((s) => ({ ...s, prefs }));
    await updateStudentProfile({ prefs });
    toast.push('Preference updated.', 'info');
  };

  return (
    <div className="stack">
      <div className="page-head">
        <h1>My Profile</h1>
        <p>Your profile is the starting point of your personalized journey. Keep it accurate so recommendations stay accurate.</p>
      </div>

      <div className="grid profile-grid">
        <div className="stack">
          <Card className="snap">
            <div className="avatar">{saved.fullName[0]}</div>
            <h3>{saved.fullName}</h3>
            <p className="muted">{saved.qualification}</p>
            <div className="row" style={{ justifyContent: 'center', marginTop: 8 }}>
              <Badge tone="primary">{saved.targetExam}</Badge><Badge tone="blue">{saved.level}</Badge>
            </div>
            <ul className="kv">
              <li><span>Available Study Time</span><b>{saved.dailyHours} hours/day</b></li>
              <li><span>Interested Field</span><b>{saved.field}</b></li>
              <li><span>Subjects</span><b>{saved.subjects.length} selected</b></li>
            </ul>
          </Card>
          <div className="quote-card"><blockquote>&ldquo;{quotes.profile}&rdquo;</blockquote></div>
        </div>

        <div className="stack">
          <Card
            title="Student Information"
            subtitle={editing ? 'Editing. Remember to save your changes.' : 'Press Edit Profile to make changes.'}
            action={!editing && <Button variant="soft" size="sm" icon={Pencil} onClick={() => setEditing(true)}>Edit Profile</Button>}
          >
            <form onSubmit={save}>
              <fieldset disabled={!editing}>
                <div className="form-grid">
                  <div className="field"><label htmlFor="name">Full Name</label>
                    <input id="name" className="input" value={form.fullName} onChange={(e) => set('fullName', e.target.value)} /></div>
                  <div className="field"><label htmlFor="qual">Qualification</label>
                    <select id="qual" className="select" value={form.qualification} onChange={(e) => set('qualification', e.target.value)}>
                      {profileOptions.qualifications.map((o) => <option key={o}>{o}</option>)}</select></div>
                  <div className="field"><label htmlFor="age">Age</label>
                    <input id="age" type="number" className="input" value={form.age} onChange={(e) => set('age', Number(e.target.value))} /></div>
                  <div className="field"><label htmlFor="target">Target Exam</label>
                    <select id="target" className="select" value={form.targetExam} onChange={(e) => set('targetExam', e.target.value)}>
                      {profileOptions.exams.map((o) => <option key={o}>{o}</option>)}</select></div>
                  <div className="field"><label htmlFor="level">Preparation Level</label>
                    <select id="level" className="select" value={form.level} onChange={(e) => set('level', e.target.value)}>
                      {profileOptions.levels.map((o) => <option key={o}>{o}</option>)}</select></div>
                  <div className="field"><label htmlFor="hours">Daily Study Time</label>
                    <select id="hours" className="select" value={form.dailyHours} onChange={(e) => set('dailyHours', Number(e.target.value))}>
                      {profileOptions.hours.map((h) => <option key={h} value={h}>{h} hour{h > 1 ? 's' : ''}/day</option>)}</select></div>
                  <div className="field"><label htmlFor="field">Interested Field</label>
                    <select id="field" className="select" value={form.field} onChange={(e) => set('field', e.target.value)}>
                      {profileOptions.fields.map((o) => <option key={o}>{o}</option>)}</select></div>
                </div>
                <div className="field" style={{ marginTop: 16 }}>
                  <span className="lbl">Preferred Subjects</span>
                  <div className="chips">
                    {profileOptions.subjects.map((s) => (
                      <button type="button" key={s} className="chip" aria-pressed={form.subjects.includes(s)} onClick={() => toggleSubject(s)}>{s}</button>
                    ))}
                  </div>
                </div>
              </fieldset>
              {editing && (
                <div className="row mt16">
                  <Button type="submit" icon={Save} disabled={saving}>{saving ? 'Saving...' : 'Save Changes'}</Button>
                  <Button variant="ghost" icon={X} onClick={cancel}>Cancel</Button>
                </div>
              )}
            </form>
          </Card>

          <Card title="Learning Preferences" subtitle="Tell Aspirixa how you like to prepare">
            <div className="pref-grid">
              {prefList.map(({ key, title, text, icon: Icon }) => (
                <div className="pref" key={key}>
                  <span className="stat-ic t-soft-primary"><Icon size={18} aria-hidden="true" /></span>
                  <div><b>{title}</b><small>{text}</small></div>
                  <Switch checked={form.prefs[key]} label={title} onChange={() => togglePref(key)} />
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function Profile() {
  const state = useAsync(getStudentProfile);
  return (
    <AsyncView state={state} loadingText="Loading your profile..." loadingSub="Fetching your saved details." errorText="Unable to load your profile. Try again.">
      {(p) => <ProfileForm initial={p} />}
    </AsyncView>
  );
}