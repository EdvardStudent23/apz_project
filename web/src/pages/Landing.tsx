import { Link, Navigate } from 'react-router-dom';
import { Button } from '@/components/Button';
import { ThemeToggle } from '@/components/ThemeToggle';
import { useAuth } from '@/auth/AuthContext';

export default function Landing() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return null;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  return (
    <div className="landing">
      <nav className="landing-nav">
        <div className="shell-brand">
          <span className="shell-brand-mark">N</span>
          <span>NanoBank</span>
        </div>
        <div className="row">
          <ThemeToggle />
          <Link to="/login">
            <Button variant="ghost">Sign in</Button>
          </Link>
          <Link to="/register">
            <Button variant="primary">Create account</Button>
          </Link>
        </div>
      </nav>

      <section className="landing-hero">
        <div className="landing-card">
          <h1>Banking, made simple.</h1>
          <p>
            Open multi-currency accounts, send money in seconds, and watch every transaction
            land in your activity feed in real time.
          </p>
          <div className="landing-actions">
            <Link to="/register">
              <Button variant="primary" size="lg">
                Get started — it's free
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="secondary" size="lg">
                I already have an account
              </Button>
            </Link>
          </div>

          <div className="feature-row">
            <div>
              <strong>USD, EUR, UAH</strong>
              <span className="muted">Auto-converts at internal rates.</span>
            </div>
            <div>
              <strong>Instant transfers</strong>
              <span className="muted">ACID-safe between accounts.</span>
            </div>
            <div>
              <strong>Live activity</strong>
              <span className="muted">Each transfer streamed to history.</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
