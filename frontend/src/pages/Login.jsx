import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogIn, UserPlus, ShieldCheck } from 'lucide-react';
import { loginUser, registerUser } from '../services/api.js';
import Logo from '../components/Logo.jsx';
import Button from '../components/Button.jsx';
import '../styles/auth.css';

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [form, setForm] = useState({ fullName: '', email: '', password: '', confirm: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const isRegister = mode === 'register';
  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const switchMode = (next) => {
    setMode(next);
    setError('');
  };

  // Same checks as the server, so the student gets quick feedback
  const validate = () => {
    if (isRegister && !form.fullName.trim()) return 'Please enter your name.';
    if (!EMAIL_PATTERN.test(form.email.trim())) return 'Please enter a valid email address.';
    if (isRegister && form.password.length < 8) return 'Password must be at least 8 characters.';
    if (!form.password) return 'Please enter your password.';
    if (isRegister && form.password !== form.confirm) return 'The two passwords do not match.';
    return '';
  };

  const submit = async (e) => {
    e.preventDefault();
    const problem = validate();
    if (problem) return setError(problem);

    setBusy(true);
    setError('');
    try {
      if (isRegister) {
        await registerUser({ fullName: form.fullName.trim(), email: form.email.trim(), password: form.password });
      } else {
        await loginUser({ email: form.email.trim(), password: form.password });
      }
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-wrap">
      <section className="card auth-card">
        <div className="auth-brand"><Logo /></div>
        <h1 className="auth-title">{isRegister ? 'Create your account' : 'Welcome back'}</h1>
        <p className="auth-sub">
          {isRegister ? 'Your progress and test history will be saved to your account.' : 'Sign in to continue your preparation.'}
        </p>

        <div className="tabs auth-tabs" role="tablist" aria-label="Sign in or create account">
          <button type="button" role="tab" className="tab" aria-selected={!isRegister} onClick={() => switchMode('login')}>Sign in</button>
          <button type="button" role="tab" className="tab" aria-selected={isRegister} onClick={() => switchMode('register')}>Create account</button>
        </div>

        <form className="auth-form" onSubmit={submit} noValidate>
          {isRegister && (
            <div className="field">
              <label htmlFor="auth-name">Full name</label>
              <input id="auth-name" className="input" autoComplete="name" value={form.fullName}
                onChange={(e) => set('fullName', e.target.value)} />
            </div>
          )}

          <div className="field">
            <label htmlFor="auth-email">Email</label>
            <input id="auth-email" type="email" className="input" autoComplete="email" value={form.email}
              onChange={(e) => set('email', e.target.value)} />
          </div>

          <div className="field">
            <label htmlFor="auth-password">Password</label>
            <input id="auth-password" type="password" className="input"
              autoComplete={isRegister ? 'new-password' : 'current-password'} value={form.password}
              onChange={(e) => set('password', e.target.value)} />
          </div>

          {isRegister && (
            <div className="field">
              <label htmlFor="auth-confirm">Confirm password</label>
              <input id="auth-confirm" type="password" className="input" autoComplete="new-password" value={form.confirm}
                onChange={(e) => set('confirm', e.target.value)} />
            </div>
          )}

          {error && <div className="auth-error" role="alert">{error}</div>}

          <Button type="submit" icon={isRegister ? UserPlus : LogIn} disabled={busy}>
            {busy ? 'Please wait...' : isRegister ? 'Create account' : 'Sign in'}
          </Button>
        </form>

        <div className="auth-foot"><ShieldCheck size={14} aria-hidden="true" /> Your password is stored only as a secure hash.</div>
      </section>
    </div>
  );
}
