import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Flag, Timer, Info, ClipboardCheck, ArrowRight, RotateCcw } from 'lucide-react';
import { useAsync } from '../hooks/useAsync.js';
import { getDiagnosticQuestions, submitDiagnosticAnswer, getDiagnosticResult } from '../services/api.js';
import { quotes } from '../data/quotes.js';
import { masteryStatus } from '../utils/helpers.js';
import { AsyncView, LoadingState, ErrorState } from '../components/EmptyState.jsx';
import AIJourney from '../components/AIJourney.jsx';
import Card from '../components/Card.jsx';
import Button from '../components/Button.jsx';
import Badge from '../components/Badge.jsx';
import ProgressBar from '../components/ProgressBar.jsx';
import MasteryBar from '../components/MasteryBar.jsx';
import QuizOption from '../components/QuizOption.jsx';
import Modal from '../components/Modal.jsx';
import { ScoreRing } from '../components/RecommendationCard.jsx';

const fmt = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
const BKT_NOTE = 'One question does not define your knowledge. Your answer sequence helps estimate your mastery.';

function Intro({ total, onStart }) {
  return (
    <Card>
      <div className="grid g3" style={{ marginBottom: 18 }}>
        {[['Questions', `${total} mixed questions`], ['Time', '15 minutes'], ['Result', 'Topic-level mastery']].map(([a, b]) => (
          <div key={a} className="pref"><div><small>{a}</small><b>{b}</b></div></div>
        ))}
      </div>
      <div className="note"><Info size={16} aria-hidden="true" /> {BKT_NOTE}</div>
      <div className="mt16"><Button icon={ClipboardCheck} onClick={onStart}>Start Assessment</Button></div>
    </Card>
  );
}

function Runner({ questions, onFinish }) {
  const [i, setI] = useState(0);
  const [answers, setAnswers] = useState({});
  const [flags, setFlags] = useState({});
  const [left, setLeft] = useState(15 * 60);
  const [confirm, setConfirm] = useState(false);
  

  const q = questions[i];
  const answered = Object.keys(answers).length;

  useEffect(() => {
    const t = setInterval(() => setLeft((s) => s - 1), 1000);
    return () => clearInterval(t);
  }, []);
  useEffect(() => { if (left === 0) onFinish(answers); }, [left]); // eslint-disable-line react-hooks/exhaustive-deps

 const choose = (idx) => {
  const selectedLetter = 'ABCD'[idx];

  setAnswers((a) => ({
    ...a,
    [q.id]: selectedLetter,
  }));

  submitDiagnosticAnswer({
    questionId: q.id,
    selected: selectedLetter,
  });
};

  const toggleFlag = () => setFlags((f) => ({ ...f, [q.id]: !f[q.id] }));
  const last = i === questions.length - 1;
  const next = () => (last ? (answered < questions.length ? setConfirm(true) : onFinish(answers)) : setI(i + 1));

  return (
    <div className="grid q-layout">
      <Card>
        <div className="q-head">
          <div>
            <span className="q-count">Question {i + 1} of {questions.length}</span>
            <ProgressBar value={Math.round(((i + 1) / questions.length) * 100)} label="Assessment progress" />
          </div>
          <span className={`timer ${left < 120 ? 'low' : ''}`} role="timer"><Timer size={15} aria-hidden="true" /> {fmt(Math.max(left, 0))}</span>
        </div>
        <div className="row"><Badge tone="primary">{q.subject}</Badge><Badge>Topic: {q.topic}</Badge></div>
        <h2 className="q-text">{q.text}</h2>
        <div className="opts" role="group" aria-label="Answer options">
  {q.options.map((o, idx) => (
    <QuizOption
      key={o}
      letter={'ABCD'[idx]}
      text={o}
      state={answers[q.id] === 'ABCD'[idx] ? 'selected' : 'idle'}
      onSelect={() => choose(idx)}
    />
  ))}
</div>
        <div className="q-actions">
          <Button variant="ghost" icon={ChevronLeft} disabled={i === 0} onClick={() => setI(i - 1)}>Previous Question</Button>
          <Button variant={flags[q.id] ? 'soft' : 'ghost'} icon={Flag} onClick={toggleFlag}>{flags[q.id] ? 'Flagged' : 'Flag Question'}</Button>
          <Button iconRight={ChevronRight} onClick={next}>{last ? 'Submit Assessment' : 'Next Question'}</Button>
        </div>
      </Card>

      <div className="stack">
        <Card title="Question palette" subtitle={`${answered} of ${questions.length} answered`}>
          <div className="palette">
            {questions.map((qq, idx) => (
  <button
    key={qq.id}
    type="button"
    aria-label={`Go to question ${idx + 1}`}
    className={`pal ${idx === i ? 'cur' : ''} ${answers[qq.id] !== undefined ? 'ans' : ''} ${flags[qq.id] ? 'flag' : ''}`}
    onClick={() => setI(idx)}
  >
    {idx + 1}
  </button>
))}
          </div>
        </Card>
        <div className="note"><Info size={16} aria-hidden="true" /> {BKT_NOTE}</div>
      </div>

      <Modal open={confirm} title="Submit assessment?" onClose={() => setConfirm(false)}
        footer={<><Button variant="ghost" onClick={() => setConfirm(false)}>Keep answering</Button><Button onClick={() => onFinish(answers)}>Submit anyway</Button></>}>
        <p>You have {questions.length - answered} unanswered question{questions.length - answered > 1 ? 's' : ''}. Unanswered questions give less information about your mastery.</p>
      </Modal>
    </div>
  );
}

function Result({ r, onRetake }) {
  return (
    <div className="stack">
      <div className="res-banner">
        <ScoreRing value={r.overall} size={116} label="Overall Mastery" />
        <div>
          <span className="eyebrow light">Assessment complete</span>
          <h2>Diagnostic Assessment Complete</h2>
          <p>You answered {r.answered} of {r.total} questions. Your answer sequence was used to estimate topic-level mastery.</p>
          <div className="row">
            <Link to="/study-plan"><Button variant="light" iconRight={ArrowRight}>Generate My Study Plan</Button></Link>
            <Button variant="outline-light" icon={RotateCcw} onClick={onRetake}>Retake</Button>
          </div>
        </div>
      </div>

      <div className="grid g2">
        <Card title="Strong Areas" subtitle="Subjects where your mastery looks good">
          {r.strong.map((s) => <MasteryBar key={s.name} label={s.name} value={s.value} />)}
        </Card>
        <Card title="Needs Attention" subtitle="Subjects that will get extra time in your plan">
          {r.attention.map((s) => <MasteryBar key={s.name} label={s.name} value={s.value} />)}
        </Card>
      </div>

      <Card title="Topics That Need Attention" subtitle="Topic-level mastery estimated from your answers">
        {r.topics.map((t) => <MasteryBar key={t.name} label={t.name} sub={t.subject} value={t.value} />)}
        <div className="note mt16"><Info size={16} aria-hidden="true" /> Weak topics are identified using estimated mastery and threshold-based analysis. Strong is 70% or more, Developing is 55-69%, and Needs Attention is below 55%. A single percentage is an estimate, not proof of mastery.</div>
      </Card>
    </div>
  );
}

export default function Diagnostic() {
  const qs = useAsync(getDiagnosticQuestions);
  const [phase, setPhase] = useState('intro'); // intro | run | loading | result | error
  const [result, setResult] = useState(null);
  const last = useRef({});

  const finish = async (answers) => {
    last.current = answers;
    setPhase('loading');
    try {
      setResult(await getDiagnosticResult(answers));
      setPhase('result');
    } catch {
      setPhase('error');
    }
  };

  return (
    <div className="stack">
      <div className="page-head">
        <h1>Let's Understand Your Current Level</h1>
        <p>This assessment helps Aspirixa AI identify topic-level strengths and weaknesses.</p>
      </div>
      <AIJourney active={3} />
      <AsyncView state={qs} loadingText="Preparing your assessment..." loadingSub="Loading questions." errorText="Unable to load the assessment. Try again.">
        {(questions) => (
          <>
            {phase === 'intro' && <Intro total={questions.length} onStart={() => setPhase('run')} />}
            {phase === 'run' && <Runner questions={questions} onFinish={finish} />}
            {phase === 'loading' && <LoadingState text="Estimating your mastery..." sub="Reading your answer sequence topic by topic." />}
            {phase === 'error' && <ErrorState text="Unable to calculate your result. Try again." onRetry={() => finish(last.current)} />}
            {phase === 'result' && result && (() => {
  const topics = (result.topic_analysis || []).map((topic, index) => {
    let value = Number(
  topic.mastery_percentage ??
  topic.mastery_probability ??
  topic.mastery ??
  topic.score_percentage ??
  topic.percentage ??
  0
);

    if (value > 0 && value <= 1) {
      value *= 100;
    }

    return {
      name:
        topic.topic ||
        topic.topic_name ||
        topic.name ||
        `Topic ${index + 1}`,
      subject: topic.subject || topic.category || '',
      value: Math.round(value),
    };
  });

  const displayResult = {
    ...result,
    overall: Number(result.score_percentage || 0),
    answered: Number(result.total_answered || 0),
    total: questions.length,
    topics,
    strong: topics.filter((t) => t.value >= 70),
    attention: topics.filter((t) => t.value < 70),
  };

  return (
    <Result
      r={displayResult}
      onRetake={() => setPhase('intro')}
    />
  );
})()}
          </>
        )}
      </AsyncView>
      <div className="quote-card"><blockquote>&ldquo;{quotes.diagnostic}&rdquo;</blockquote></div>
    </div>
  );
}