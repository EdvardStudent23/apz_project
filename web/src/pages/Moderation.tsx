import { useCallback, useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { ApiError } from '@/api/client';
import { listPendingProducts, moderateProduct } from '@/api/shop';
import { Product } from '@/api/types';
import { useAuth } from '@/auth/AuthContext';
import { AppShell } from '@/components/AppShell';
import { Banner } from '@/components/Banner';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Input } from '@/components/Input';
import { Spinner } from '@/components/Spinner';
import { formatMoney } from '@/lib/format';

export default function Moderation() {
  const { user, loading } = useAuth();
  const [products, setProducts] = useState<Product[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [working, setWorking] = useState<string | null>(null);
  const [notes, setNotes] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    try {
      setProducts(await listPendingProducts());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load pending listings.');
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) return null;
  if (!user?.is_admin) return <Navigate to="/dashboard" replace />;

  const onDecide = async (id: string, decision: 'approved' | 'rejected') => {
    setWorking(id);
    setError(null);
    try {
      await moderateProduct(id, decision, notes[id] || undefined);
      await load();
      setNotes((n) => {
        const next = { ...n };
        delete next[id];
        return next;
      });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not moderate the listing.');
    } finally {
      setWorking(null);
    }
  };

  return (
    <AppShell>
      <div className="stack" style={{ gap: 'var(--space-6)' }}>
        <div className="row-between">
          <h1>Moderation queue</h1>
          <Button variant="secondary" onClick={() => void load()}>Refresh</Button>
        </div>

        {error && <Banner tone="error">{error}</Banner>}

        {products === null ? (
          <div className="empty-state"><Spinner size="lg" /></div>
        ) : products.length === 0 ? (
          <div className="empty-state">Nothing pending. 🎉</div>
        ) : (
          <div className="stack">
            {products.map((p) => (
              <Card key={p.id}>
                <div className="stack">
                  <div className="row-between" style={{ alignItems: 'flex-start' }}>
                    <div className="stack-sm" style={{ flex: 1 }}>
                      <h3 style={{ margin: 0 }}>{p.name}</h3>
                      <div className="muted mono" style={{ fontSize: 'var(--fs-xs)' }}>
                        by {p.owner_id} · listed {new Date(p.created_at).toLocaleString()}
                      </div>
                      {p.description && <div>{p.description}</div>}
                    </div>
                    <div style={{ fontWeight: 700, whiteSpace: 'nowrap' }}>
                      {formatMoney(p.price, p.currency)}
                    </div>
                  </div>
                  <Input
                    label="Moderation note (optional)"
                    value={notes[p.id] ?? ''}
                    onChange={(e) => setNotes((n) => ({ ...n, [p.id]: e.target.value }))}
                    placeholder="Reason for rejection or any feedback"
                    maxLength={300}
                  />
                  <div className="row" style={{ justifyContent: 'flex-end' }}>
                    <Button
                      variant="danger"
                      onClick={() => onDecide(p.id, 'rejected')}
                      loading={working === p.id}
                    >
                      Reject
                    </Button>
                    <Button
                      onClick={() => onDecide(p.id, 'approved')}
                      loading={working === p.id}
                    >
                      Approve
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
