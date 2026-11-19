import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { BookOpen, PlayCircle, ListChecks, Newspaper, RotateCcw, Lightbulb, Clock, Search } from 'lucide-react';
import { useAsync } from '../hooks/useAsync.js';
import { getResources, addToPlan } from '../services/api.js';
import { diffTone } from '../utils/helpers.js';
import { useToast } from '../components/Toast.jsx';
import { AsyncView, EmptyState } from '../components/EmptyState.jsx';
import Card from '../components/Card.jsx';
import Button from '../components/Button.jsx';
import Badge from '../components/Badge.jsx';
import Modal from '../components/Modal.jsx';

const catIcons = {
  'Concept Notes': BookOpen, 'Video Lessons': PlayCircle, 'Practice Sets': ListChecks,
  'Current Affairs': Newspaper, 'Revision Material': RotateCcw, 'Exam Strategy': Lightbulb,
};

export default function Resources() {
  const state = useAsync(getResources);
  const toast = useToast();
  const [params, setParams] = useSearchParams();
  const [cat, setCat] = useState('All');
  const [open, setOpen] = useState(null);
  const q = params.get('q') || '';

  const addPlan = async (r) => {
    await addToPlan({ subject: r.subject, topic: r.title, minutes: r.minutes });
    toast.push(`"${r.title}" was added to your study plan.`);
  };
  const start = (r) => toast.push(`Starting: ${r.title}`, 'info');

  return (
    <div className="stack">
      <div className="page-head">
        <h1>Resources</h1>
        <p>Notes, videos and practice sets organised by what you need to learn next.</p>
      </div>

      <AsyncView state={state} loadingText="Loading resources..." loadingSub="Finding material for your topics." errorText="Unable to load resources. Try again.">
        {({ items, categories }) => {
          const list = items.filter((r) =>
            (cat === 'All' || r.category === cat) &&
            `${r.title} ${r.subject} ${r.topic}`.toLowerCase().includes(q.toLowerCase()));
          return (
            <>
              <div className="row between">
                <div className="tabs" role="tablist" aria-label="Resource categories">
                  {['All', ...categories].map((c) => (
                    <button key={c} role="tab" aria-selected={cat === c} className="tab" onClick={() => setCat(c)}>{c}</button>
                  ))}
                </div>
                <div className="tb-search" style={{ width: 260 }}>
                  <Search size={16} aria-hidden="true" />
                  <input value={q} onChange={(e) => setParams(e.target.value ? { q: e.target.value } : {})} placeholder="Filter resources..." aria-label="Filter resources" />
                </div>
              </div>

              {list.length === 0 ? (
                <EmptyState title="No resources match" text="Try a different category or search word." action={<Button variant="soft" onClick={() => { setCat('All'); setParams({}); }}>Clear filters</Button>} />
              ) : (
                <div className="grid g3">
                  {list.map((r) => {
                    const Icon = catIcons[r.category] || BookOpen;
                    return (
                      <Card key={r.id} className="res-card hover">
                        <div className="row between">
                          <span className="stat-ic t-soft-primary" style={{ width: 38, height: 38 }}><Icon size={18} aria-hidden="true" /></span>
                          <Badge tone={diffTone[r.difficulty]}>{r.difficulty}</Badge>
                        </div>
                        <h4>{r.title}</h4>
                        <div className="row"><Badge tone="primary">{r.subject}</Badge><Badge>{r.topic}</Badge></div>
                        <div className="res-meta"><span>{r.type}</span><span><Clock size={13} aria-hidden="true" /> {r.minutes} min</span></div>
                        <div className="res-actions">
                          <Button size="sm" variant="ghost" onClick={() => setOpen(r)}>Open</Button>
                          <Button size="sm" onClick={() => start(r)}>Start Learning</Button>
                          <Button size="sm" variant="soft" onClick={() => addPlan(r)}>Add to Plan</Button>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              )}
            </>
          );
        }}
      </AsyncView>

      <Modal open={!!open} title={open ? open.title : ''} onClose={() => setOpen(null)}
        footer={open && <><Button variant="soft" onClick={() => { addPlan(open); setOpen(null); }}>Add to Plan</Button><Button onClick={() => { start(open); setOpen(null); }}>Start Learning</Button></>}>
        {open && (
          <>
            <div className="row"><Badge tone="primary">{open.subject}</Badge><Badge>{open.topic}</Badge><Badge tone={diffTone[open.difficulty]}>{open.difficulty}</Badge></div>
            <p style={{ margin: '12px 0' }}>{open.summary}</p>
            <p className="muted">{open.type} &middot; about {open.minutes} minutes &middot; {open.category}</p>
          </>
        )}
      </Modal>
    </div>
  );
}