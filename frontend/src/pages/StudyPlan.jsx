import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Target, Trophy, Flame, Repeat, Scale, History, ClipboardCheck } from 'lucide-react';
import { useAsync } from '../hooks/useAsync.js';
import { getStudyPlan, updatePlanStatus } from '../services/api.js';
import { quotes } from '../data/quotes.js';
import { AsyncView, EmptyState } from '../components/EmptyState.jsx';
import AIJourney from '../components/AIJourney.jsx';
import StatCard from '../components/StatCard.jsx';
import Card from '../components/Card.jsx';
import Button from '../components/Button.jsx';
import Badge from '../components/Badge.jsx';
import ProgressBar from '../components/ProgressBar.jsx';
import StudyTimeline from '../components/StudyTimeline.jsx';

const whyIcons = [Target, Clock, Repeat, Scale, History];
const colors = ['#5B4FE9', '#4F8DF7', '#20A779', '#D69E2E', '#E85D75'];

export default function StudyPlan() {
  const state = useAsync(getStudyPlan);
  const [items, setItems] = useState(null);

  useEffect(() => {
    if (state.data) {
      const schedule = (state.data.schedule || []).map((item, index) => ({
  ...item,
  id: item.id || index + 1,

  time: `${9 + index}:00`,
  period: index < 2 ? 'AM' : 'PM',

  subject: item.subject || item.topic || 'General Practice',
  topic: item.topic || 'General Practice',

  minutes: Number(item.minutes || 0),

  status: item.status || (index === 0 ? 'current' : 'upcoming'),

  weak: item.priority === 'High',
  extra: false,
}));

      setItems(schedule);
    }
  }, [state.data]);

  const toggle = (id) => {
    const item = items?.find((i) => i.id === id);

    if (!item) return;

    const status =
      item.status === 'completed'
        ? 'upcoming'
        : 'completed';

    setItems((list) =>
      list.map((i) =>
        i.id === id ? { ...i, status } : i
      )
    );

    updatePlanStatus(id, status);
  };

  return (
    <AsyncView
      state={state}
      loadingText="Building your plan..."
      loadingSub="Your personalized study plan is being prepared."
      errorText="Unable to load your study plan. Try again."
      isEmpty={(d) => !d || !(d.schedule || []).length}
      empty={
        <EmptyState
          icon={ClipboardCheck}
          title="Your study plan is locked"
          text="Complete the diagnostic assessment to unlock your study plan."
          action={
            <Link to="/diagnostic">
              <Button>Take Diagnostic Test</Button>
            </Link>
          }
        />
      }
    >
      {(d) => {
        const list = items || d.schedule || [];

        const total = list.reduce(
          (sum, item) => sum + Number(item.minutes || 0),
          0
        );

        const dailyHours = (
          Number(d.totalMinutes || total) / 60
        ).toFixed(1);

        const weakTopics = list.filter(
          (item) => item.priority === 'High'
        ).length;

        const completed = list.filter(
          (item) => item.status === 'completed'
        ).length;

        const weeklyGoal = Math.round(
          Number(d.totalMinutes || total) / 60 * 7
        );

        const weeklyDone = Math.round(
          (completed / Math.max(list.length, 1)) *
          weeklyGoal
        );

        const weeklyPct = Math.min(
          100,
          Math.round(
            (weeklyDone / Math.max(weeklyGoal, 1)) * 100
          )
        );

        const bySubject = Object.values(
          list.reduce((acc, item) => {
            const name =
              item.subject ||
              item.topic ||
              'General Practice';

            if (!acc[name]) {
              acc[name] = {
                name,
                minutes: 0,
              };
            }

            acc[name].minutes += Number(
              item.minutes || 0
            );

            return acc;
          }, {})
        );

        const why = [
          {
            title: 'Weak topics get priority',
            text: 'More study time is allocated to topics identified during your diagnostic assessment.',
          },
          {
            title: 'Based on available time',
            text: `Your plan uses approximately ${dailyHours} hours of available daily study time.`,
          },
          {
            title: 'Practice is included',
            text: 'The remaining study time is used for general practice and preparation.',
          },
          {
            title: 'Revision is scheduled',
            text: 'A dedicated revision session is included to reinforce previously learned topics.',
          },
          {
            title: 'Adaptive preparation',
            text: `The current preparation level is ${d.preparationLevel || 'beginner'}.`,
          },
        ];

        const flow = [
          'Diagnostic assessment',
          'BKT mastery estimation',
          'Weak-topic detection',
          'Time allocation',
          'Personalized study schedule',
          'Revision and practice',
        ];

        return (
          <div className="stack">

            <div className="page-head">
              <h1>Your Personalized Study Plan</h1>
              <p>
                Built from your available time, weak topics,
                preparation level and syllabus coverage.
              </p>
            </div>

            <AIJourney active={4} />

            <div className="grid g4">

              <StatCard
                icon={Clock}
                label="Daily Study Time"
                value={dailyHours}
                unit=" hrs"
                tone="primary"
              />

              <StatCard
                icon={Target}
                label="Priority Topics"
                value={weakTopics}
                tone="amber"
              />

              <StatCard
                icon={Trophy}
                label="Weekly Goal"
                value={weeklyGoal}
                unit=" hrs"
                tone="blue"
              />

              <StatCard
                icon={Flame}
                label="Consistency"
                value={weeklyPct}
                unit="%"
                tone="green"
              />

            </div>

            <div className="grid g-main">

              <Card
                title="Today's Schedule"
                subtitle={`${total} minutes planned`}
              >

                <StudyTimeline
                  items={list}
                  onToggle={toggle}
                />

                {total > 0 && (
                  <div className="mt16">

                    <div
                      className="alloc"
                      role="img"
                      aria-label="Time allocation by subject"
                    >
                      {bySubject.map((subject, index) => (
                        <i
                          key={subject.name}
                          style={{
                            width: `${(
                              subject.minutes / total
                            ) * 100}%`,
                            background:
                              colors[
                                index % colors.length
                              ],
                          }}
                        />
                      ))}
                    </div>

                    <div className="row">

                      {bySubject.map(
                        (subject, index) => (
                          <span
                            key={subject.name}
                            className="row"
                            style={{
                              gap: 6,
                              fontSize: 12,
                            }}
                          >
                            <i
                              style={{
                                width: 9,
                                height: 9,
                                borderRadius: 3,
                                background:
                                  colors[
                                    index %
                                      colors.length
                                  ],
                              }}
                            />

                            {subject.name}{' '}
                            {subject.minutes} min
                          </span>
                        )
                      )}

                    </div>

                  </div>
                )}

              </Card>

              <div className="stack">

                <Card title="Weekly goal">

                  <ProgressBar
                    value={weeklyPct}
                    size="lg"
                    text={`${weeklyDone} of ${weeklyGoal} hours this week`}
                    label="Weekly goal progress"
                  />

                </Card>

                <Card title="Why this plan?">

                  <ul className="why-list">

                    {why.map((item, index) => {

                      const Icon =
                        whyIcons[index];

                      return (
                        <li key={item.title}>

                          <span
                            className="stat-ic t-soft-primary"
                            style={{
                              width: 34,
                              height: 34,
                            }}
                          >
                            <Icon
                              size={16}
                              aria-hidden="true"
                            />
                          </span>

                          <div>
                            <b>
                              {index + 1}.{' '}
                              {item.title}
                            </b>

                            <small>
                              {item.text}
                            </small>
                          </div>

                        </li>
                      );
                    })}

                  </ul>

                </Card>

              </div>

            </div>

            <Card
              title="How your plan is built"
              subtitle="The same flow runs every day, using your latest mastery"
            >

              <div
                className="grid g-main"
                style={{
                  alignItems: 'center',
                }}
              >

                <ol className="flow">

                  {flow.map((step) => (
                    <li key={step}>
                      {step}
                    </li>
                  ))}

                </ol>

                <div className="stack">

                  <div className="row">

                    <Badge tone="primary">
                      Constraint-based time allocation
                    </Badge>

                    <Badge tone="primary">
                      Weak-topic prioritization
                    </Badge>

                    <Badge tone="primary">
                      Revision scheduling
                    </Badge>

                  </div>

                  <div className="quote-card">

                    <blockquote>
                      &ldquo;
                      {quotes.studyPlan}
                      &rdquo;
                    </blockquote>

                  </div>

                </div>

              </div>

            </Card>

          </div>
        );
      }}
    </AsyncView>
  );
}