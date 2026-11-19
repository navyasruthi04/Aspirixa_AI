import { useEffect, useRef, useState } from 'react';
import { Sparkles, Info, Compass } from 'lucide-react';
import { useAsync } from '../hooks/useAsync.js';
import { getStudentProfile, getExamRecommendations } from '../services/api.js';
import { profileOptions } from '../data/studentData.js';
import { useToast } from '../components/Toast.jsx';
import { AsyncView, EmptyState, LoadingState, ErrorState } from '../components/EmptyState.jsx';
import AIJourney from '../components/AIJourney.jsx';
import Card from '../components/Card.jsx';
import Button from '../components/Button.jsx';
import Badge from '../components/Badge.jsx';
import ProgressBar from '../components/ProgressBar.jsx';
import { ScoreRing, factorLabels } from '../components/RecommendationCard.jsx';

const eligUI = {
  eligible: { tone: 'green', label: '\u2713 Eligible' },
  check: { tone: 'amber', label: 'Check specific requirements' },
  'not-eligible': { tone: 'red', label: 'Not eligible' },
};

const explain = (e, hours) =>
  `${e.name} suits you because your qualification meets its eligibility rules (${e.factors.qualification}%), your preferred subjects align with its syllabus (${e.factors.subject}%), and ${hours} hour${hours > 1 ? 's' : ''} of daily study fits the preparation it needs (${e.factors.time}%).`;

function Recommender({ profile }) {
  const toast = useToast();
  const resultsRef = useRef(null);
  const [form, setForm] = useState({
    qualification: profile.qualification, age: profile.age, field: profile.field, targetExam: profile.targetExam,
    level: profile.level, dailyHours: profile.dailyHours, subjects: profile.subjects,
  });
  const [phase, setPhase] = useState('form'); // form | loading | result | error
  const [result, setResult] = useState(null);
  const [selId, setSelId] = useState(null);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const toggleSubject = (s) => set('subjects', form.subjects.includes(s) ? form.subjects.filter((x) => x !== s) : [...form.subjects, s]);

  useEffect(() => {
    if (phase === 'result' && resultsRef.current) resultsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [phase]);

  const generate = async (e) => {
    e.preventDefault();
    if (!form.subjects.length) return toast.push('Select at least one preferred subject.', 'warning');
    setPhase('loading');
    try {
      const r = await getExamRecommendations(form);
      setResult(r);
      setSelId(r.top ? r.top.id : null);
      setPhase('result');
      toast.push('Your recommendation is ready.');
    } catch {
      setPhase('error');
    }
  };

  const selected = result && result.ranked.find((r) => r.id === selId);
  const scale = selected && result.top ? selected.suitability / result.top.suitability : 1;

  return (
    <div className="stack">
      <div className="page-head">
        <h1>Find the Government Exam That Fits You</h1>
        <p>Aspirixa AI analyzes your eligibility, preferences, preparation level and available study time before recommending suitable exams.</p>
      </div>
      <AIJourney active={2} />

      <Card title="Step 1: Your profile inputs" subtitle="Change anything to see how the recommendation changes">
        <form onSubmit={generate}>
          <div className="form-grid">
            <div className="field"><label htmlFor="r-qual">Qualification</label>
              <select id="r-qual" className="select" value={form.qualification} onChange={(e) => set('qualification', e.target.value)}>
                {profileOptions.qualifications.map((o) => <option key={o}>{o}</option>)}</select></div>
            <div className="field"><label htmlFor="r-age">Age</label>
              <input id="r-age" type="number" min="16" max="45" className="input" value={form.age} onChange={(e) => set('age', Number(e.target.value))} /></div>
            <div className="field"><label htmlFor="r-field">Preferred Field</label>
              <select id="r-field" className="select" value={form.field} onChange={(e) => set('field', e.target.value)}>
                {profileOptions.fields.map((o) => <option key={o}>{o}</option>)}</select></div>
            <div className="field"><label htmlFor="r-target">Target / Interested Exam</label>
              <select id="r-target" className="select" value={form.targetExam} onChange={(e) => set('targetExam', e.target.value)}>
                {profileOptions.exams.map((o) => <option key={o}>{o}</option>)}</select></div>
            <div className="field"><label htmlFor="r-level">Preparation Level</label>
              <select id="r-level" className="select" value={form.level} onChange={(e) => set('level', e.target.value)}>
                {profileOptions.levels.map((o) => <option key={o}>{o}</option>)}</select></div>
            <div className="field"><label htmlFor="r-hours">Daily Study Time</label>
              <select id="r-hours" className="select" value={form.dailyHours} onChange={(e) => set('dailyHours', Number(e.target.value))}>
                {profileOptions.hours.map((h) => <option key={h} value={h}>{h} hour{h > 1 ? 's' : ''}/day</option>)}</select></div>
          </div>
          <div className="field" style={{ marginTop: 16 }}>
            <span className="lbl">Subject Preferences</span>
            <div className="chips">
              {profileOptions.subjects.map((s) => (
                <button type="button" key={s} className="chip" aria-pressed={form.subjects.includes(s)} onClick={() => toggleSubject(s)}>{s}</button>
              ))}
            </div>
          </div>
          <div className="mt16">
            <Button type="submit" icon={Sparkles} disabled={phase === 'loading'}>Generate AI Recommendation</Button>
          </div>
        </form>
      </Card>

      <div ref={resultsRef} className="stack">
        {phase === 'form' && (
          <EmptyState icon={Compass} title="Your recommendation will appear here" text="Fill in your profile and press Generate AI Recommendation. You will see eligibility, ranking and the reasons." />
        )}
        {phase === 'loading' && <LoadingState text="Analyzing your profile..." sub="Your personalized recommendation is being prepared." />}
        {phase === 'error' && <ErrorState text="Unable to generate your recommendation. Try again." onRetry={generate} />}

        {phase === 'result' && result && (
          <>
            <div className="step-h"><span>2</span><div><h3>Eligibility Analysis</h3><p>Exams are filtered by age and qualification rules before any prediction is made.</p></div></div>
            <div className="grid g3">
              {result.eligibility.map((e) => (
                <Card key={e.id} className="elig hover">
                  <h4>{e.name}</h4>
                  <Badge tone={eligUI[e.status].tone}>{eligUI[e.status].label}</Badge>
                  <p>{e.note}</p>
                </Card>
              ))}
            </div>
            <div className="note"><Info size={16} aria-hidden="true" /> Eligibility rules shown here are indicative. Always verify with the official exam notification.</div>

            <div className="step-h"><span>3</span><div><h3>Suitability Ranking</h3><p>Select an exam on the right to see how it scores for you.</p></div></div>
            {!selected ? (
              <EmptyState title="No eligible exams found" text="Try changing your qualification or age to see matching exams." />
            ) : (
              <div className="grid g-main">
                <Card>
                  <div className="feat">
                    <ScoreRing value={selected.suitability} size={110} />
                    <div>
                      <span className="eyebrow"><Sparkles size={14} aria-hidden="true" /> {selected.id === result.top.id ? 'Top recommendation' : 'Selected exam'}</span>
                      <h2>{selected.name}</h2>
                      <p className="muted">{selected.suitability}% Suitability</p>
                    </div>
                  </div>
                  <div className="feat-bars">
                    {Object.entries(factorLabels).map(([k, label]) => (
                      <ProgressBar key={k} text={label} value={selected.factors[k]} showValue />
                    ))}
                  </div>
                </Card>
                <Card title="Ranked for you">
                  {result.ranked.map((r, i) => (
                    <button key={r.id} type="button" className="rank" aria-pressed={r.id === selId} onClick={() => setSelId(r.id)}>
                      <span className="rank-n">{i + 1}</span>
                      <div><div className="row between"><b>{r.name}</b><b>{r.suitability}%</b></div><ProgressBar value={r.suitability} size="sm" label={`${r.name} suitability`} /></div>
                    </button>
                  ))}
                </Card>
              </div>
            )}

            {selected && (
              <>
                <div className="step-h"><span>4</span><div><h3>Why did Aspirixa AI recommend this?</h3><p>Each bar shows how much a factor pushed the score up or down.</p></div></div>
                <Card>
                  <p style={{ marginBottom: 12 }}>{explain(selected, form.dailyHours)}</p>
                  {result.shap.map((s) => {
                    const v = +(s.value * scale).toFixed(2);
                    const style = { width: `${Math.min(Math.abs(v) / 0.4, 1) * 50}%`, ...(v >= 0 ? { left: '50%' } : { right: '50%' }) };
                    return (
                      <div className="shap-row" key={s.label}>
                        <span>{s.label}</span>
                        <div className="shap-track" role="img" aria-label={`${s.label} contribution ${v}`}>
                          <i className="shap-zero" /><b className={v >= 0 ? 'sh-pos' : 'sh-neg'} style={style} />
                        </div>
                        <em>{v > 0 ? '+' : ''}{v.toFixed(2)}</em>
                      </div>
                    );
                  })}
                  <p className="muted" style={{ fontSize: 12.5, marginTop: 12 }}>
                    Recommendation generated using eligibility filtering, suitability prediction, multi-criteria ranking and explainable AI.
                  </p>
                  <div className="algos">
                    {result.algorithms.map((a) => <div className="algo" key={a.name}><b>{a.name}</b><small>{a.role}</small></div>)}
                  </div>
                  <div className="note mt16"><Info size={16} aria-hidden="true" /> These are sample demo values. Real suitability scores and SHAP contributions will come from the backend once it is connected.</div>
                </Card>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function ExamRecommendation() {
  const state = useAsync(getStudentProfile);
  return (
    <AsyncView state={state} loadingText="Loading your profile..." loadingSub="Getting your details ready." errorText="Unable to load your profile. Try again.">
      {(p) => <Recommender profile={p} />}
    </AsyncView>
  );
}