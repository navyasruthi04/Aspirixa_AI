import { useState } from 'react';
import { CheckCircle2, Brain, ListChecks, Clock, Lightbulb } from 'lucide-react';
import { useAsync } from '../hooks/useAsync.js';
import { getPerformanceAnalytics } from '../services/api.js';
import { quotes } from '../data/quotes.js';
import { masteryStatus } from '../utils/helpers.js';
import { AsyncView } from '../components/EmptyState.jsx';
import AIJourney from '../components/AIJourney.jsx';
import StatCard from '../components/StatCard.jsx';
import Card from '../components/Card.jsx';
import ChartCard from '../components/ChartCard.jsx';
import MasteryBar from '../components/MasteryBar.jsx';
import { LineChart, BarChart, DonutChart } from '../components/Charts.jsx';

const icons = { acc: CheckCircle2, mastery: Brain, solved: ListChecks, hours: Clock };

export default function Performance() {
  const state = useAsync(getPerformanceAnalytics);
  const [tab, setTab] = useState('City');

  return (
    <AsyncView state={state} loadingText="Crunching your numbers..." loadingSub="Your performance report is being prepared." errorText="Unable to load your performance data. Try again.">
      {(d) => (
        <div className="stack">
          <div className="page-head">
            <h1>Performance Analytics</h1>
            <p>Accuracy, mastery, consistency and topic-level progress in one place.</p>
          </div>
          <AIJourney active={6} />

          <div className="grid g4">
            {d.summary.map((s) => <StatCard key={s.id} icon={icons[s.id]} label={s.label} value={s.value} unit={s.unit} trend={s.trend} tone={s.tone} />)}
          </div>

          <div className="grid g2">
            <ChartCard title="Weekly Accuracy" subtitle="Quiz accuracy for the last 7 days">
              <LineChart values={d.weekly.values} labels={d.weekly.labels} />
            </ChartCard>
            <ChartCard title="Subject Mastery" subtitle="Estimated mastery by subject">
              <BarChart items={d.subjects.map((s) => ({ label: s.short, value: s.value, tone: masteryStatus(s.value).tone }))} />
            </ChartCard>
            <ChartCard title="Study Time" subtitle="Hours studied each day">
              <BarChart items={d.studyTime.labels.map((l, i) => ({ label: l, value: d.studyTime.values[i], tone: 'primary' }))} max={4} unit="h" />
            </ChartCard>
            <ChartCard title="Question Difficulty" subtitle="What you have practised so far">
              <DonutChart items={d.difficulty} />
            </ChartCard>
          </div>

          <div className="grid g-main">
            <Card title="Subject Mastery Status" subtitle="Strong is 70% or more. Needs Attention is below 55%.">
              {d.subjects.map((s) => <MasteryBar key={s.name} label={s.name} value={s.value} />)}
              <h4 style={{ margin: '18px 0 4px', fontSize: 13 }}>Topic-level analysis</h4>
              {d.topics.map((t) => <MasteryBar key={t.name} label={t.name} sub={t.subject} value={t.value} />)}
            </Card>

            <div className="stack">
              <Card title="AI Learning Insights" icon={Lightbulb} subtitle="Sample insights until backend analytics are connected">
                <ul className="why-list">
                  {d.insights.map((t) => <li key={t}><div><b style={{ fontWeight: 600 }}>{t}</b></div></li>)}
                </ul>
              </Card>
              <Card title="Leaderboard" subtitle="Optional and secondary. Compare only if it motivates you.">
                <div className="tabs" role="tablist" style={{ marginBottom: 10 }}>
                  {Object.keys(d.leaderboard).map((k) => (
                    <button key={k} role="tab" aria-selected={tab === k} className="tab" onClick={() => setTab(k)}>{k}</button>
                  ))}
                </div>
                <ul className="lb">
                  {d.leaderboard[tab].map((p) => (
                    <li key={p.name} className={p.me ? 'me' : ''}><b>{p.rank}</b>{p.name}<span>{p.xp} XP</span></li>
                  ))}
                </ul>
              </Card>
              <div className="quote-card"><blockquote>&ldquo;{quotes.performance}&rdquo;</blockquote></div>
            </div>
          </div>
        </div>
      )}
    </AsyncView>
  );
}