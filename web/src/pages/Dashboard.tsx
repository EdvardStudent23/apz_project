import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { closeAccount, listAccounts } from '@/api/accounts';
import { listHistoryByUser } from '@/api/history';
import { Account, HistoryEntry } from '@/api/types';
import { useAuth } from '@/auth/AuthContext';
import { AccountTile, AddAccountTile } from '@/components/AccountTile';
import { AppShell } from '@/components/AppShell';
import { Banner } from '@/components/Banner';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Spinner } from '@/components/Spinner';
import { TransactionRow } from '@/components/TransactionRow';
import { ApiError } from '@/api/client';

function sameAccounts(a: Account[], b: Account[]): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i += 1) {
    const x = a[i]!;
    const y = b[i]!;
    if (
      x.id !== y.id
      || x.balance !== y.balance
      || (x.held_balance ?? 0) !== (y.held_balance ?? 0)
      || (x.available_balance ?? 0) !== (y.available_balance ?? 0)
      || (x.closed_at ?? null) !== (y.closed_at ?? null)
    ) {
      return false;
    }
  }
  return true;
}

function sameHistory(a: HistoryEntry[], b: HistoryEntry[]): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i += 1) {
    const x = a[i]!;
    const y = b[i]!;
    if (x.timestamp !== y.timestamp || x.amount !== y.amount || x.sender_id !== y.sender_id || x.receiver_id !== y.receiver_id) {
      return false;
    }
  }
  return true;
}

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [initialLoad, setInitialLoad] = useState(true);
  const [pulse, setPulse] = useState(false);
  const [closingId, setClosingId] = useState<string | null>(null);
  const inFlight = useRef(false);

  const accountIds = useMemo(() => new Set(accounts.map((a) => a.id)), [accounts]);

  const refresh = useCallback(
    async ({ silent = false }: { silent?: boolean } = {}) => {
      if (!user) return;
      if (inFlight.current) return;
      inFlight.current = true;
      if (!silent) setInitialLoad(true);
      setError(null);
      try {
        const [accs, hist] = await Promise.all([
          listAccounts(),
          listHistoryByUser(user.id).catch(() => [] as HistoryEntry[]),
        ]);
        // Only update state if the payload actually changed — avoids React
        // re-renders that would interrupt the user mid-interaction.
        setAccounts((prev) => (sameAccounts(prev, accs) ? prev : accs));
        setHistory((prev) => (sameHistory(prev, hist) ? prev : hist));
        if (silent) {
          setPulse(true);
          setTimeout(() => setPulse(false), 400);
        }
      } catch (e) {
        if (!silent) setError(e instanceof ApiError ? e.message : 'Could not load your data.');
      } finally {
        inFlight.current = false;
        if (!silent) setInitialLoad(false);
      }
    },
    [user],
  );

  // Initial load
  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Live updates: poll every 5s while the tab is visible, and re-fetch on
  // focus / visibility change so changes from other tabs or the /transfer
  // screen show up immediately.
  useEffect(() => {
    const tick = () => {
      if (document.visibilityState === 'visible') void refresh({ silent: true });
    };
    const onVisible = () => {
      if (document.visibilityState === 'visible') void refresh({ silent: true });
    };
    const intervalId = window.setInterval(tick, 5000);
    document.addEventListener('visibilitychange', onVisible);
    window.addEventListener('focus', onVisible);
    return () => {
      window.clearInterval(intervalId);
      document.removeEventListener('visibilitychange', onVisible);
      window.removeEventListener('focus', onVisible);
    };
  }, [refresh]);

  const totalsByCurrency = useMemo(() => {
    const totals = new Map<string, number>();
    for (const a of accounts) {
      if (a.closed_at) continue;
      totals.set(a.currency, (totals.get(a.currency) ?? 0) + a.balance);
    }
    return Array.from(totals.entries());
  }, [accounts]);

  const heldByCurrency = useMemo(() => {
    const held = new Map<string, number>();
    for (const a of accounts) {
      if (a.closed_at) continue;
      const h = Number(a.held_balance ?? 0);
      if (h > 0) held.set(a.currency, (held.get(a.currency) ?? 0) + h);
    }
    return Array.from(held.entries());
  }, [accounts]);

  const recent = history.slice(0, 5);

  return (
    <AppShell>
      <div className="stack" style={{ gap: 'var(--space-6)' }}>
        <div className="row-between">
          <div>
            <h1 style={{ marginBottom: 4 }}>
              Hi, {user?.username} 👋
              <span
                aria-hidden
                style={{
                  display: 'inline-block',
                  marginLeft: 10,
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: pulse ? 'var(--color-success)' : 'transparent',
                  transition: 'background 400ms ease',
                  verticalAlign: 'middle',
                }}
                title="Live"
              />
            </h1>
            <p className="muted" style={{ margin: 0 }}>
              {totalsByCurrency.length === 0
                ? 'Open an account to start moving money.'
                : totalsByCurrency
                    .map(([cur, amt]) => `${amt.toFixed(2)} ${cur}`)
                    .join(' · ')}
            </p>
            {heldByCurrency.length > 0 && (
              <p
                style={{
                  margin: '4px 0 0',
                  color: 'var(--color-warn)',
                  fontSize: 'var(--fs-sm)',
                }}
                title="Funds reserved for pending orders or holds"
              >
                🔒 On hold:{' '}
                {heldByCurrency
                  .map(([cur, amt]) => `${amt.toFixed(2)} ${cur}`)
                  .join(' · ')}
              </p>
            )}
          </div>
          <div className="row">
            <Button variant="secondary" onClick={() => navigate('/history')}>
              View activity
            </Button>
            <Button variant="primary" onClick={() => navigate('/transfer')}>
              Send money
            </Button>
          </div>
        </div>

        {error && <Banner tone="error">{error}</Banner>}

        <section>
          <div className="section-title-row">
            <h2>Accounts</h2>
            <Link to="/accounts/new">
              <Button variant="ghost">+ New account</Button>
            </Link>
          </div>

          {initialLoad ? (
            <div className="empty-state">
              <Spinner size="lg" />
            </div>
          ) : (
            <div className="account-grid">
              {accounts.map((a) => (
                <AccountTile
                  key={a.id}
                  account={a}
                  onClose={async () => {
                    if (!window.confirm(`Close this ${a.currency} account?`)) return;
                    setClosingId(a.id);
                    setError(null);
                    try {
                      await closeAccount(a.id);
                      await refresh();
                    } catch (e) {
                      setError(e instanceof Error ? e.message : 'Could not close the account.');
                    } finally {
                      setClosingId(null);
                    }
                  }}
                  closing={closingId === a.id}
                />
              ))}
              <AddAccountTile onClick={() => navigate('/accounts/new')} />
            </div>
          )}
        </section>

        <section>
          <Card>
            <div className="card-header">
              <h3>Recent activity</h3>
              <Link to="/history" className="muted">
                See all →
              </Link>
            </div>
            {initialLoad ? (
              <div className="empty-state">
                <Spinner />
              </div>
            ) : recent.length === 0 ? (
              <div className="empty-state">
                Your transfers will appear here. Try sending money between two of your accounts.
              </div>
            ) : (
              <div className="txn-list">
                {recent.map((h, i) => (
                  <TransactionRow
                    key={`${h.timestamp}-${i}`}
                    entry={h}
                    perspective={accountIds.has(h.sender_id) ? 'out' : 'in'}
                  />
                ))}
              </div>
            )}
          </Card>
        </section>
      </div>
    </AppShell>
  );
}
