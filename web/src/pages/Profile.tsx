import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listAccounts } from '@/api/accounts';
import { ApiError, request } from '@/api/client';
import { Account } from '@/api/types';
import { useAuth } from '@/auth/AuthContext';
import { AppShell } from '@/components/AppShell';
import { Banner } from '@/components/Banner';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Spinner } from '@/components/Spinner';
import { formatMoney, initials } from '@/lib/format';

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="row-between" style={{ alignItems: 'flex-start', gap: 16, padding: '10px 0', borderBottom: '1px solid var(--color-border)' }}>
      <span className="muted" style={{ minWidth: 140 }}>{label}</span>
      <span style={{ textAlign: 'right', flex: 1, overflowWrap: 'anywhere' }}>{value}</span>
    </div>
  );
}

export default function Profile() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState<Account[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [signOutEverywhereBusy, setSignOutEverywhereBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    listAccounts()
      .then((accs) => {
        if (!cancelled) setAccounts(accs);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof ApiError ? e.message : 'Could not load your accounts.');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const totals = useMemo(() => {
    if (!accounts) return [];
    const map = new Map<string, number>();
    for (const a of accounts) {
      if (a.closed_at) continue;
      map.set(a.currency, (map.get(a.currency) ?? 0) + a.balance);
    }
    return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
  }, [accounts]);

  const openCount = accounts?.filter((a) => !a.closed_at).length ?? 0;
  const closedCount = accounts?.filter((a) => a.closed_at).length ?? 0;

  const onSignOutEverywhere = async () => {
    if (!window.confirm('Sign out of every device for this account?')) return;
    setSignOutEverywhereBusy(true);
    try {
      // Best-effort: server revokes all sessions for this user.
      await request('/auth/logout?all_devices=true', { method: 'POST' }).catch(() => {});
    } finally {
      await signOut();
      navigate('/', { replace: true });
    }
  };

  if (!user) return null;

  return (
    <AppShell>
      <div className="stack" style={{ gap: 'var(--space-6)', maxWidth: 720, margin: '0 auto' }}>
        <div className="row" style={{ gap: 'var(--space-4)', alignItems: 'center' }}>
          <span
            className="user-avatar"
            style={{ width: 56, height: 56, fontSize: 'var(--fs-xl)' }}
          >
            {initials(user.username)}
          </span>
          <div>
            <h1 style={{ margin: 0 }}>{user.username}</h1>
            <div className="muted">
              {user.is_admin ? 'Administrator' : 'Member'} · since{' '}
              {new Date(user.created_at).toLocaleDateString()}
            </div>
          </div>
        </div>

        {error && <Banner tone="error">{error}</Banner>}

        <Card>
          <h3>Profile</h3>
          <Field label="Username" value={<span className="mono">{user.username}</span>} />
          <Field label="Email" value={<span className="mono">{user.email}</span>} />
          <Field label="User ID" value={<span className="mono">{user.id}</span>} />
          <Field
            label="Status"
            value={
              <span className={`banner ${user.is_active ? 'banner-success' : 'banner-warn'}`} style={{ padding: '2px 8px', borderRadius: 999, fontSize: 12 }}>
                {user.is_active ? 'active' : 'inactive'}
              </span>
            }
          />
          <Field
            label="Role"
            value={
              <span className={`banner ${user.is_admin ? 'banner-info' : 'banner-success'}`} style={{ padding: '2px 8px', borderRadius: 999, fontSize: 12 }}>
                {user.is_admin ? 'admin' : 'user'}
              </span>
            }
          />
          <Field label="Member since" value={new Date(user.created_at).toLocaleString()} />
        </Card>

        <Card>
          <h3>Accounts</h3>
          {accounts === null ? (
            <div className="empty-state">
              <Spinner />
            </div>
          ) : (
            <>
              <Field label="Open accounts" value={openCount} />
              <Field label="Closed accounts" value={closedCount} />
              <Field
                label="Total balances"
                value={
                  totals.length === 0
                    ? <span className="muted">no funds</span>
                    : (
                      <div className="stack-sm" style={{ alignItems: 'flex-end' }}>
                        {totals.map(([cur, amt]) => (
                          <span key={cur} className="mono">{formatMoney(amt, cur)}</span>
                        ))}
                      </div>
                    )
                }
              />
              <div style={{ marginTop: 'var(--space-4)' }}>
                <Button onClick={() => navigate('/accounts/new')}>+ Open another account</Button>
              </div>
            </>
          )}
        </Card>

        <Card>
          <h3>Security</h3>
          <Field
            label="Sessions"
            value={
              <Button
                variant="danger"
                onClick={onSignOutEverywhere}
                loading={signOutEverywhereBusy}
              >
                Sign out everywhere
              </Button>
            }
          />
        </Card>
      </div>
    </AppShell>
  );
}
