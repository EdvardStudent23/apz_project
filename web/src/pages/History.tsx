import { useCallback, useEffect, useMemo, useState } from 'react';
import { listAccounts } from '@/api/accounts';
import { listHistoryByAccount, listHistoryByUser } from '@/api/history';
import { ApiError } from '@/api/client';
import { Account, HistoryEntry } from '@/api/types';
import { AppShell } from '@/components/AppShell';
import { Banner } from '@/components/Banner';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Select } from '@/components/Select';
import { Spinner } from '@/components/Spinner';
import { TransactionRow } from '@/components/TransactionRow';
import { useAuth } from '@/auth/AuthContext';

const ALL = 'all';

export default function History() {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [filter, setFilter] = useState<string>(ALL);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const accountIds = useMemo(() => new Set(accounts.map((a) => a.id)), [accounts]);

  const load = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const fetched =
        filter === ALL
          ? await listHistoryByUser(user.id)
          : await listHistoryByAccount(filter);
      setEntries(fetched);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load history.');
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, [user, filter]);

  useEffect(() => {
    let cancelled = false;
    listAccounts()
      .then((a) => {
        if (!cancelled) setAccounts(a);
      })
      .catch(() => {
        /* surfaced via filter list being empty */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <AppShell>
      <div className="stack" style={{ gap: 'var(--space-6)' }}>
        <div className="row-between">
          <h1>Activity</h1>
          <Button variant="secondary" onClick={() => void load()}>
            Refresh
          </Button>
        </div>

        <Card>
          <div className="stack">
            <Select
              label="Filter"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value={ALL}>All my activity</option>
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.currency} · {a.id.slice(0, 8)}…
                </option>
              ))}
            </Select>

            {error && <Banner tone="error">{error}</Banner>}

            {loading ? (
              <div className="empty-state">
                <Spinner size="lg" />
              </div>
            ) : entries.length === 0 ? (
              <div className="empty-state">No transactions yet.</div>
            ) : (
              <div className="txn-list">
                {entries.map((h, i) => (
                  <TransactionRow
                    key={`${h.timestamp}-${i}`}
                    entry={h}
                    perspective={accountIds.has(h.sender_id) ? 'out' : 'in'}
                  />
                ))}
              </div>
            )}
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
