import { FormEvent, useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { Banner } from '@/components/Banner';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Input } from '@/components/Input';
import { useAuth } from '@/auth/AuthContext';
import { ApiError } from '@/api/client';
import { validateEmail, validatePassword, validateUsername } from '@/lib/validators';

export default function Register() {
  const { signUp, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!loading && isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const usernameError = username ? validateUsername(username) : null;
  const emailError = email ? validateEmail(email) : null;
  const passwordError = password
    ? validatePassword(password, { username, email })
    : null;

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    const u = validateUsername(username);
    if (u) return setError(u);
    const m = validateEmail(email);
    if (m) return setError(m);
    const p = validatePassword(password, { username, email });
    if (p) return setError(p);

    setBusy(true);
    try {
      await signUp(username.trim().toLowerCase(), email.trim().toLowerCase(), password);
      navigate('/dashboard', { replace: true });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Registration failed. Try again.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page-center">
      <div className="page-narrow stack">
        <Card>
          <div className="stack">
            <div>
              <h1 style={{ marginBottom: 4 }}>Create your account</h1>
              <p className="muted">It only takes a moment.</p>
            </div>

            {error && <Banner tone="error">{error}</Banner>}

            <form onSubmit={onSubmit} className="stack" noValidate>
              <Input
                label="Username"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="johndoe"
                hint="Letters, digits and underscore. 3–50 characters. Cannot start with a digit."
                error={usernameError ?? undefined}
                autoFocus
              />
              <Input
                label="Email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="john@example.com"
                error={emailError ?? undefined}
              />
              <Input
                label="Password"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 8 characters"
                hint="Upper + lower + digit + special character. Must not contain your username or email."
                error={passwordError ?? undefined}
              />
              <Button type="submit" loading={busy} block size="lg">
                Create account
              </Button>
            </form>
          </div>
        </Card>
        <p className="center muted">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
