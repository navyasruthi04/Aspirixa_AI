import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, ArrowRight, RotateCcw, Check, X } from 'lucide-react';
import { getAdaptiveQuestion, submitQuizAnswer } from '../services/api.js';
import { diffTone, masteryStatus } from '../utils/helpers.js';
import { useToast } from '../components/Toast.jsx';
import { LoadingState, ErrorState } from '../components/EmptyState.jsx';
import AIJourney from '../components/AIJourney.jsx';
import Card from '../components/Card.jsx';
import Button from '../components/Button.jsx';
import Badge from '../components/Badge.jsx';
import ProgressBar from '../components/ProgressBar.jsx';
import QuizOption from '../components/QuizOption.jsx';

const TOTAL = 6;
const START = 58;
const levels = ['Easy', 'Moderate', 'Difficult'];

export default function AdaptiveQuiz() {
  const toast = useToast();
  const [round, setRound] = useState(1);
  const [mastery, setMastery] = useState(START);
  const [q, setQ] = useState(null);
  const [reason, setReason] = useState('');
  const [status, setStatus] = useState('loading'); // loading | ready | error
  const [selected, setSelected] = useState(null);
  const [fb, setFb] = useState(null);
  const [history, setHistory] = useState([]);
  const [done, setDone] = useState(false);

  const load = useCallback(async (difficulty, usedIds, m) => {
    setStatus('loading');
    try {
      const r = await getAdaptiveQuestion({ difficulty, usedIds, mastery: m });
      setQ(r.question); setReason(r.reason); setStatus('ready');
    } catch {
      setStatus('error');
    }
  }, []);

  useEffect(() => { load('Moderate', [], START); }, [load]);

  const answer = async (idx) => {
    if (fb) return;
    setSelected(idx);
    try {
      const r = await submitQuizAnswer({ questionId: q.id, selected: idx, mastery });
      setFb(r);
      setMastery(r.masteryAfter);
      setHistory((h) => [...h, { id: q.id, round, topic: q.topic, difficulty: q.difficulty, correct: r.correct, before: r.masteryBefore, after: r.masteryAfter }]);
    } catch {
      setSelected(null);
      toast.push('Could not submit your answer. Try again.', 'warning');
    }
  };

  const next = () => {
    if (round === TOTAL) return setDone(true);
    setRound((r) => r + 1);
    setSelected(null);
    const nd = fb.nextDifficulty;
    setFb(null);
    load(nd, history.map((h) => h.id), mastery);
  };

  const restart = () => {
    setRound(1); setMastery(START); setSelected(null); setFb(null); setHistory([]); setDone(false);
    load('Moderate', [], START);
  };

  const optState = (i) => {
    if (!fb) return selected === i ? 'selected' : 'idle';
    if (i === fb.correctIndex) return 'correct';
    if (i === selected) return 'wrong';
    return 'idle';
  };

  if (done) {
    const right = history.filter((h) => h.correct).length;
    return (
      <div className="stack">
        <div className="page-head"><h1>Quiz Summary</h1><p>Here is how your mastery moved during this adaptive session.</p></div>
        <div className="grid g3">
          <Card><small className="muted">Correct answers</small><div className="streak-big">{right}<small> / {TOTAL}</small></div></Card>
          <Card><small className="muted">Mastery change</small><div className="streak-big">{START}% &rarr; {mastery}%</div></Card>
          <Card><small className="muted">Final level</small><div className="mt8"><Badge tone={masteryStatus(mastery).tone}>{masteryStatus(mastery).label}</Badge></div></Card>
        </div>
        <Card title="Round by round">
          <ul className="hist">
            {history.map((h) => (
              <li key={h.id}>
                {h.correct ? <Check size={15} color="#20A779" aria-label="Correct" /> : <X size={15} color="#E85D75" aria-label="Wrong" />}
                Q{h.round} &middot; {h.topic} <Badge tone={diffTone[h.difficulty]}>{h.difficulty}</Badge><b>{h.before}% &rarr; {h.after}%</b>
              </li>
            ))}
          </ul>
        </Card>
        <div className="row">
          <Button icon={RotateCcw} onClick={restart}>Start Another Session</Button>
          <Link to="/performance"><Button variant="ghost" iconRight={ArrowRight}>View Performance</Button></Link>
        </div>
      </div>
    );
  }

  const currentDiff = q ? q.difficulty : 'Moderate';

  return (
    <div className="stack">
      <div className="page-head">
        <h1>Adaptive Quiz</h1>
        <p>Every question is chosen from your current mastery estimate, so the quiz changes as you learn.</p>
      </div>
      <AIJourney active={5} />

      <Card className="quiz-top">
        <div><small>Progress</small><strong>Question {round} / {TOTAL}</strong></div>
        <div><small>Current Difficulty</small><Badge tone={diffTone[currentDiff]}>{currentDiff}</Badge></div>
        <div><ProgressBar value={mastery} tone={masteryStatus(mastery).tone} text="Mastery" showValue /></div>
      </Card>

      <div className="grid quiz-grid">
        <Card>
          {status === 'loading' && <LoadingState text="Selecting your next question..." sub="Choosing difficulty from your mastery." />}
          {status === 'error' && <ErrorState text="Unable to load the question. Try again." onRetry={() => load('Moderate', history.map((h) => h.id), mastery)} />}
          {status === 'ready' && q && (
            <>
              <div className="row"><Badge tone="primary">{q.subject}</Badge><Badge>Topic: {q.topic}</Badge></div>
              <h2 className="q-text">{q.text}</h2>
              <div className="opts" role="group" aria-label="Answer options">
                {q.options.map((o, i) => (
                  <QuizOption key={o} letter={'ABCD'[i]} text={o} state={optState(i)} disabled={!!fb} onSelect={() => answer(i)} />
                ))}
              </div>
              {fb && (
                <div className={`fb ${fb.correct ? 'ok' : 'review'}`} role="status">
                  <strong>{fb.correct ? 'Correct \u2713' : 'Review this concept'}</strong>
                  <p>{fb.explanation}</p>
                  <div className="fb-grid">
                    <div><small>Mastery updated</small><b>{fb.masteryBefore}% &rarr; {fb.masteryAfter}%</b></div>
                    <div><small>Next question difficulty</small><b>{q.difficulty} &rarr; {fb.nextDifficulty}</b></div>
                  </div>
                  <Button iconRight={ArrowRight} onClick={next}>{round === TOTAL ? 'View Summary' : 'Next Question'}</Button>
                </div>
              )}
            </>
          )}
        </Card>

        <div className="stack">
          <Card title="Why this question?" icon={Sparkles}>
            <p style={{ fontSize: 13 }}>{reason || 'Selecting a question that matches your current mastery...'}</p>
            <div className="scale" aria-label="Difficulty scale">
              {levels.map((l) => <div key={l} className={`seg ${l === currentDiff ? 'on' : ''}`}>{l}</div>)}
            </div>
            <small className="muted">Below 40% mastery: Easy. 40-60%: Moderate. Above 60%: Difficult.</small>
          </Card>
          <Card title="This session">
            {history.length === 0 ? <p className="muted" style={{ fontSize: 13 }}>Your answers will appear here as you go.</p> : (
              <ul className="hist">
                {history.map((h) => (
                  <li key={h.id}>{h.correct ? <Check size={14} color="#20A779" aria-label="Correct" /> : <X size={14} color="#E85D75" aria-label="Wrong" />}Q{h.round} &middot; {h.topic}<b>{h.after}%</b></li>
                ))}
              </ul>
            )}
          </Card>
          <div className="note">Mastery and difficulty values here follow a simple demo rule. The real values will come from the backend BKT model.</div>
        </div>
      </div>
    </div>
  );
}