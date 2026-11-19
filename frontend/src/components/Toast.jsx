import { createContext, useCallback, useContext, useState } from 'react';
import { CheckCircle2, AlertTriangle, Info } from 'lucide-react';

const ToastContext = createContext({ push: () => {} });
export const useToast = () => useContext(ToastContext);

const icons = { success: CheckCircle2, warning: AlertTriangle, info: Info };

export function ToastProvider({ children }) {
  const [items, setItems] = useState([]);

  const push = useCallback((message, tone = 'success') => {
    const id = Date.now() + Math.random();
    setItems((l) => [...l, { id, message, tone }]);
    setTimeout(() => setItems((l) => l.filter((t) => t.id !== id)), 3200);
  }, []);

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div className="toasts" aria-live="polite">
        {items.map((t) => {
          const Icon = icons[t.tone] || Info;
          return <div key={t.id} className={`toast tn-${t.tone}`}><Icon size={16} aria-hidden="true" />{t.message}</div>;
        })}
      </div>
    </ToastContext.Provider>
  );
}