import { Inbox, AlertTriangle, RefreshCw } from 'lucide-react';
import Button from './Button.jsx';

export function EmptyState({ icon: Icon = Inbox, title, text, action }) {
  return (
    <div className="state-box">
      <span className="state-ic"><Icon size={24} aria-hidden="true" /></span>
      <h3>{title}</h3>
      <p>{text}</p>
      {action}
    </div>
  );
}

export function LoadingState({ text = 'Analyzing your profile...', sub = 'Your personalized view is being prepared.' }) {
  return (
    <div className="state-box" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <h3>{text}</h3>
      <p>{sub}</p>
      <div className="skel-row"><i /><i /><i /></div>
    </div>
  );
}

export function ErrorState({ text = 'Something went wrong. Try again.', onRetry }) {
  return (
    <div className="state-box" role="alert">
      <span className="state-ic err"><AlertTriangle size={24} aria-hidden="true" /></span>
      <h3>{text}</h3>
      <p>Check your connection and try once more.</p>
      {onRetry && <Button variant="soft" icon={RefreshCw} onClick={onRetry}>Retry</Button>}
    </div>
  );
}

// Handles loading / error / empty / success in one place.
// state = result of useAsync(). children = function that receives the data.
export function AsyncView({ state, loadingText, loadingSub, errorText, isEmpty, empty, children }) {
  if (state.status === 'loading') return <LoadingState text={loadingText} sub={loadingSub} />;
  if (state.status === 'error') return <ErrorState text={errorText} onRetry={state.reload} />;
  if (isEmpty && isEmpty(state.data)) return empty;
  return children(state.data);
}