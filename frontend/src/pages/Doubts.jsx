import { useEffect, useState } from 'react';
import { MessageSquare, Send, Clock } from 'lucide-react';
import { useAsync } from '../hooks/useAsync.js';
import { getDoubts, postDoubt } from '../services/api.js';
import { profileOptions } from '../data/studentData.js';
import { useToast } from '../components/Toast.jsx';
import { AsyncView, EmptyState } from '../components/EmptyState.jsx';
import Card from '../components/Card.jsx';
import Button from '../components/Button.jsx';
import Badge from '../components/Badge.jsx';

const tone = { Solved: 'green', Active: 'blue', Open: 'amber' };

export default function Doubts() {
  const state = useAsync(getDoubts);
  const toast = useToast();
  const [list, setList] = useState(null);
  const [text, setText] = useState('');
  const [subject, setSubject] = useState(profileOptions.subjects[0]);
  const [filter, setFilter] = useState('All');
  const [openId, setOpenId] = useState(null);
  const [posting, setPosting] = useState(false);

  useEffect(() => { if (state.data) setList(state.data); }, [state.data]);

  const post = async () => {
    if (text.trim().length < 10) return toast.push('Describe your doubt in a few more words.', 'warning');
    setPosting(true);
    try {
      const d = await postDoubt({ text: text.trim(), subject });
      setList((l) => [d, ...(l || [])]);
      setText('');
      toast.push('Doubt posted. The community will reply soon.');
    } catch {
      toast.push('Could not post your doubt. Try again.', 'warning');
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="stack">
      <div className="page-head">
        <h1>Doubts &amp; Community</h1>
        <p>Ask what you are stuck on and learn from other aspirants.</p>
      </div>

      <Card title="Ask a Doubt">
        <div className="field">
          <label htmlFor="doubt">What are you stuck on?</label>
          <textarea id="doubt" className="textarea" value={text} onChange={(e) => setText(e.target.value)} placeholder="Write your doubt clearly. For example: Why does a 20% increase followed by a 20% decrease not return the original value?" />
        </div>
        <div className="row between mt16">
          <div className="field" style={{ minWidth: 220 }}>
            <label htmlFor="d-sub">Subject</label>
            <select id="d-sub" className="select" value={subject} onChange={(e) => setSubject(e.target.value)}>
              {profileOptions.subjects.map((s) => <option key={s}>{s}</option>)}
            </select>
          </div>
          <Button icon={Send} onClick={post} disabled={posting}>{posting ? 'Posting...' : 'Post Doubt'}</Button>
        </div>
      </Card>

      <AsyncView state={state} loadingText="Loading discussions..." loadingSub="Fetching recent doubts." errorText="Unable to load discussions. Try again.">
        {(initial) => {
          const items = (list || initial).filter((d) => filter === 'All' || d.status === filter);
          return (
            <Card title="Recent Discussions"
              action={<div className="tabs" role="tablist">{['All', 'Solved', 'Active', 'Open'].map((s) => <button key={s} role="tab" aria-selected={filter === s} className="tab" onClick={() => setFilter(s)}>{s}</button>)}</div>}>
              {items.length === 0 ? (
                <EmptyState icon={MessageSquare} title="No discussions here yet" text="Be the first to ask a doubt in this category." />
              ) : items.map((d) => (
                <div className="doubt" key={d.id}>
                  <button className="doubt-top" aria-expanded={openId === d.id} onClick={() => setOpenId(openId === d.id ? null : d.id)}>
                    <div>
                      <strong>{d.title}</strong>
                      <div className="doubt-meta">
                        <span>{d.author}</span><span><Clock size={12} aria-hidden="true" /> {d.time}</span>
                        <span><MessageSquare size={12} aria-hidden="true" /> {d.replies} replies</span><span>{d.subject}</span>
                      </div>
                    </div>
                    <Badge tone={tone[d.status]}>{d.status}</Badge>
                  </button>
                  {openId === d.id && (
                    <div className="doubt-body">{d.preview || 'No replies yet. Be the first to help.'}</div>
                  )}
                </div>
              ))}
            </Card>
          );
        }}
      </AsyncView>
    </div>
  );
}