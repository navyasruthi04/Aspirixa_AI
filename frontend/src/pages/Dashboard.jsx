import { Link, useNavigate } from 'react-router-dom';
import { Target, CheckCircle2, Flame, Clock, ListChecks, ClipboardCheck, Zap, CalendarCheck, FileText, ArrowRight, Medal } from 'lucide-react';
import { useAsync } from '../hooks/useAsync.js';
import { getDashboard } from '../services/api.js';
import { greeting } from '../utils/helpers.js';
import { quotes } from '../data/quotes.js';
import { AsyncView } from '../components/EmptyState.jsx';
import AIJourney from '../components/AIJourney.jsx';
import StatCard from '../components/StatCard.jsx';
import Card from '../components/Card.jsx';
import Button from '../components/Button.jsx';
import RecommendationCard from '../components/RecommendationCard.jsx';
import StudyTimeline from '../components/StudyTimeline.jsx';

const statIcons = { progress: Target, accuracy: CheckCircle2, streak: Flame, time: Clock, solved: ListChecks };
const badgeIcons = { 'First Diagnostic': ClipboardCheck, '7-Day Streak': Flame, '100 Questions': ListChecks, 'Weak Topic Crusher': Target, 'Consistency Champion': Medal };
const quick = [
  { to: '/diagnostic', title: 'Take Diagnostic Test', text: 'Find your weak topics', icon: ClipboardCheck },
  { to: '/adaptive-quiz', title: 'Continue Adaptive Quiz', text: 'Questions that match your mastery', icon: Zap },
  { to: '/study-plan', title: 'View Study Plan', text: "Today's personalized schedule", icon: CalendarCheck },
  { to: '/pyqs', title: 'Practice PYQs', text: 'Exam-style questions by topic', icon: FileText },
];
const days = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];

export default function Dashboard() {
  const navigate = useNavigate();
  const state = useAsync(getDashboard);

  return (
    <AsyncView state={state} loadingText="Analyzing your profile..." loadingSub="Your personalized dashboard is being prepared." errorText="Unable to load your dashboard. Try again.">
      {(d) => (
        <div className="stack">
          <section className="hero">
            <div className="hero-grid">
              <div>
                <span className="eyebrow light">Your Exam. Your Path.</span>
                <h1>{greeting()}, {d.student.fullName}!</h1>
                <p className="sub">Let's turn your preparation into progress.</p>
                <p className="txt">Aspirixa AI understands your profile, identifies where you need improvement, and helps you follow a preparation path built around you.</p>
                <div className="row">
                  <Button variant="light" iconRight={ArrowRight} onClick={() => navigate('/adaptive-quiz')}>Continue Preparation</Button>
                  <Button variant="outline-light" onClick={() => navigate('/study-plan')}>View Study Plan</Button>
                </div>
              </div>
              <div className="hero-journey">
                <span className="hj-t">From confusion to a personalized preparation journey</span>
                <AIJourney active={5} dark compact />
              </div>
            </div>
          </section>

          <div className="grid g5">
            {d.stats.map((s) => <StatCard key={s.id} icon={statIcons[s.id]} label={s.label} value={s.value} unit={s.unit} trend={s.trend} tone={s.tone} />)}
          </div>

          <div className="grid g-main">
            <RecommendationCard
              rec={d.recommendation}
              action={<div className="row mt16"><Link className="link-btn" to="/exam-recommendation">See full analysis &rarr;</Link></div>}
            />
            <Card title="Today's Focus" subtitle="Your sessions for today" action={<Link className="link-btn" to="/study-plan">Full plan</Link>}>
              <StudyTimeline items={d.today} compact />
            </Card>
          </div>

          <h3 className="sec-t">Quick actions</h3>
          <div className="grid g4">
            {quick.map(({ to, title, text, icon: Icon }) => (
              <Link key={to} to={to} className="card card-link row" style={{ flexWrap: 'nowrap' }}>
                <span className="stat-ic t-soft-primary"><Icon size={19} aria-hidden="true" /></span>
                <div style={{ flex: 1 }}><strong>{title}</strong><div className="muted" style={{ fontSize: 12 }}>{text}</div></div>
                <ArrowRight size={16} className="muted" aria-hidden="true" />
              </Link>
            ))}
          </div>

          <div className="grid g-main">
            <Card title="Achievements" subtitle="Small milestones that show steady effort">
              <div className="ach-grid">
                {d.achievements.map((a) => {
                  const Icon = badgeIcons[a.label] || Medal;
                  return (
                    <div key={a.id} className={`ach ${a.earned ? '' : 'locked'}`}>
                      <span className="stat-ic t-soft-amber"><Icon size={18} aria-hidden="true" /></span>
                      <b>{a.label}</b><small>{a.note}</small>
                    </div>
                  );
                })}
              </div>
            </Card>
            <div className="stack">
              <Card title="Study Streak">
                <div className="streak-big">{d.student.streak} <small>days in a row</small></div>
                <div className="sdots">{days.map((day, i) => <span key={i}><i />{day}</span>)}</div>
              </Card>
              <div className="quote-card"><blockquote>&ldquo;{quotes.dashboard}&rdquo;</blockquote></div>
            </div>
          </div>
        </div>
      )}
    </AsyncView>
  );
}