import { Check, X } from 'lucide-react';

// state: idle | selected | correct | wrong
export default function QuizOption({ letter, text, state = 'idle', disabled, onSelect }) {
  return (
    <button type="button" className={`opt opt-${state}`} disabled={disabled} onClick={onSelect} aria-pressed={state === 'selected'}>
      <span className="opt-l">
        {state === 'correct' ? <Check size={14} aria-label="Correct" /> : state === 'wrong' ? <X size={14} aria-label="Wrong" /> : letter}
      </span>
      <span>{text}</span>
    </button>
  );
}