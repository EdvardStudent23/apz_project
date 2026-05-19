import { Link } from 'react-router-dom';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { useAuth } from '@/auth/AuthContext';

export default function NotFound() {
  const { isAuthenticated } = useAuth();
  return (
    <div className="page-center">
      <div className="page-narrow">
        <Card>
          <div className="stack center">
            <h1>Page not found</h1>
            <p className="muted">The link you followed doesn't exist (or doesn't exist anymore).</p>
            <Link to={isAuthenticated ? '/dashboard' : '/'}>
              <Button>{isAuthenticated ? 'Back to dashboard' : 'Back to home'}</Button>
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
