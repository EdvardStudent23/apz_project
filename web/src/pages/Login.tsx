import { FormEvent, useState } from 'react';
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { Banner } from '@/components/Banner';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Input } from '@/components/Input';
import { useAuth } from '@/auth/AuthContext';
import { ApiError } from '@/api/client';

interface LocationState {
  registeredAs?: string;
}

export default function Login() {
  const { signIn, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const next = params.get('next');

  const initialUser = (location.state as LocationState | null)?.registeredAs ?? '';
  const justRegistered = Boolean((location.state as LocationState | null)?.registeredAs);

  const [username, setUsername] = useState(initialUser);
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!loading && isAuthenticated) {
    return <Navigate to={safeNext(next) ?? '/dashboard'} replace />;
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!username || !password) {
      setError('Enter your username and password.');
      return;
    }
    setBusy(true);
    try {
      await signIn(username.trim(), password);
      navigate(safeNext(next) ?? '/dashboard', { replace: true });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Sign-in failed. Try again.');
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
              <h1 style={{ marginBottom: 4 }}>Welcome back</h1>
              <p className="muted">Sign in to continue.</p>
            </div>

            {justRegistered && (
              <Banner tone="success">
                Account created. Sign in to start using NanoBank.
              </Banner>
            )}
            {error && <Banner tone="error">{error}</Banner>}

            <form onSubmit={onSubmit} className="stack" noValidate>
              <Input
                label="Username"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="johndoe"
                autoFocus={!initialUser}
              />
              <Input
                label="Password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
              <Button type="submit" loading={busy} block size="lg">
                Sign in
              </Button>
            </form>
          </div>
        </Card>
        <p className="center muted">
          New here? <Link to="/register">Create an account</Link>
        </p>
      </div>
    </div>
  );
}

function safeNext(value: string | null): string | null {
  if (!value) return null;
  try {
    const decoded = decodeURIComponent(value);
    if (decoded.startsWith('/') && !decoded.startsWith('//')) return decoded;
    return null;
  } catch {
    return null;
  }
}
