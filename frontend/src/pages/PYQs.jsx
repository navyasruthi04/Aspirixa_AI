import { useState } from 'react';
import { useAsync } from '../hooks/useAsync.js';
import { getPYQs, checkPYQAnswer, addToPlan } from '../services/api.js';
import { diffTone } from '../utils/helpers.js';
import { useToast } from '../components/Toast.jsx';
import { AsyncView, EmptyState } from '../components/EmptyState.jsx';
import Card from '../components/Card.jsx';
import Button from '../components/Button.jsx';
import Badge from '../components/Badge.jsx';
import Modal from '../components/Modal.jsx';

const uniq = (arr, k) => [...new Set(arr.map((x) => x[k]))];
const blank = { exam: 'All', year: 'All', subject: 'All', topic: 'All', difficulty: 'All' };

export default function PYQs() {
  const state = useAsync(getPYQs);
  const toast = useToast();
  const [f, setF] = useState(blank);
  const [active, setActive] = useState(null);
  const [answer, setAnswer] = useState('');
  const [res, setRes] = useState(null);

  const openPractice = (p) => { setActive(p); setAnswer(''); setRes(null); };
  const check = async () => {
    if (!answer.trim()) return toast.push('Type your answer first.', 'warning');
    setRes(await checkPYQAnswer({ id: active.id, answer }));
  };
  const addPlan = async (p) => {
    await addToPlan({ subject: p.subject, topic: `PYQ: ${p.topic}`, minutes: 20 });
    toast.push(`${p.topic} PYQ added to your study plan.`);
  };

  return (
    <div className="stack">
      <div className="page-head">
        <h1>Previous Year Questions</h1>
        <p>Practise exam-style questions filtered by exam, year, subject, topic and difficulty.</p>
      </div>

      <AsyncView state={state} loadingText="Loading questions..." loadingSub="Opening the question bank." errorText="Unable to load questions. Try again.">
        {(items) => {
          const filters = [
            ['exam', 'Exam', uniq(items, 'exam')], ['year', 'Year', uniq(items, 'year').sort((a, b) => b - a)],
            ['subject', 'Subject', uniq(items, 'subject')], ['topic', 'Topic', uniq(items, 'topic')],
            ['difficulty', 'Difficulty', uniq(items, 'difficulty')],
          ];
          const list = items.filter((p) => filters.every(([k]) => f[k] === 'All' || String(p[k]) === String(f[k])));
          return (
            <>
              <Card>
                <div className="filters">
                  {filters.map(([k, label, opts]) => (
                    <div className="field" key={k}>
                      <label htmlFor={`f-${k}`}>{label}</label>
                      <select id={`f-${k}`} className="select" value={f[k]} onChange={(e) => setF({ ...f, [k]: e.target.value })}>
                        <option>All</option>{opts.map((o) => <option key={o}>{o}</option>)}
                      </select>
                    </div>
                  ))}
                  <Button variant="ghost" onClick={() => setF(blank)}>Reset</Button>
                </div>
              </Card>
              <div className="note">These are sample PYQ-style questions for the prototype. A verified question bank will be loaded from the backend later.</div>

              {list.length === 0 ? (
                <EmptyState title="No questions found" text="Try removing a filter to see more questions." action={<Button variant="soft" onClick={() => setF(blank)}>Reset filters</Button>} />
              ) : (
                <div>
                  <div className="pyq-head" aria-hidden="true"><span>Exam</span><span>Subject / Topic</span><span>Level</span><span>Question</span><span /></div>
                  {list.map((p) => (
                    <div className="pyq-row" key={p.id}>
                      <div><b>{p.exam}</b><small>{p.year}</small></div>
                      <div><b>{p.subject}</b><small>{p.topic}</small></div>
                      <div><Badge tone={diffTone[p.difficulty]}>{p.difficulty}</Badge></div>
                      <p>{p.question}</p>
                      <div className="pyq-act">
                        <Button size="sm" onClick={() => openPractice(p)}>Practice</Button>
                        <Button size="sm" variant="soft" onClick={() => addPlan(p)}>Add to Study Plan</Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          );
        }}
      </AsyncView>

      <Modal open={!!active} title={active ? `${active.exam} ${active.year} \u00b7 ${active.topic}` : ''} onClose={() => setActive(null)}
        footer={<><Button variant="ghost" onClick={() => setActive(null)}>Close</Button><Button onClick={check}>Check Answer</Button></>}>
        {active && (
          <>
            <p style={{ margin: '8px 0 14px', fontWeight: 600 }}>{active.question}</p>
            <div className="field">
              <label htmlFor="pyq-ans">Your answer</label>
              <input id="pyq-ans" className="input" value={answer} onChange={(e) => setAnswer(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && check()} />
            </div>
            {res && (
              <div className={`fb ${res.correct ? 'ok' : 'review'}`} role="status">
                <strong>{res.correct ? 'Correct \u2713' : 'Review this concept'}</strong>
                <p>Answer: <b>{res.answer}</b>. {res.hint}</p>
              </div>
            )}
          </>
        )}
      </Modal>
    </div>
  );
}