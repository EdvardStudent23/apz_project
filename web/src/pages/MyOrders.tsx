import { useCallback, useEffect, useState } from 'react';
import { ApiError } from '@/api/client';
import { cancelOrder, listMyOrders } from '@/api/shop';
import { Order } from '@/api/types';
import { AppShell } from '@/components/AppShell';
import { Banner } from '@/components/Banner';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Spinner } from '@/components/Spinner';
import { formatMoney } from '@/lib/format';

export default function MyOrders() {
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setOrders(await listMyOrders());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load your orders.');
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const onCancel = async (id: string) => {
    setCancelling(id);
    setError(null);
    try {
      await cancelOrder(id);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not cancel the order.');
    } finally {
      setCancelling(null);
    }
  };

  return (
    <AppShell>
      <div className="stack" style={{ gap: 'var(--space-6)' }}>
        <div className="row-between">
          <h1>My orders</h1>
          <Button variant="secondary" onClick={() => void load()}>Refresh</Button>
        </div>

        {error && <Banner tone="error">{error}</Banner>}

        {orders === null ? (
          <div className="empty-state"><Spinner size="lg" /></div>
        ) : orders.length === 0 ? (
          <div className="empty-state">You haven't placed any orders yet.</div>
        ) : (
          <div className="stack">
            {orders.map((o) => (
              <Card key={o.id}>
                <div className="row-between" style={{ alignItems: 'flex-start' }}>
                  <div className="stack-sm" style={{ minWidth: 0 }}>
                    <div className="row" style={{ gap: 'var(--space-3)' }}>
                      <strong>Order {o.id.slice(0, 8)}…</strong>
                      <span className={`banner banner-${o.status === 'cancelled' ? 'error' : 'success'}`} style={{ padding: '2px 8px', borderRadius: 999, fontSize: 12 }}>
                        {o.status === 'placed' ? 'funds held' : 'cancelled'}
                      </span>
                    </div>
                    <div className="muted mono" style={{ fontSize: 'var(--fs-xs)' }}>
                      Product {o.product_id}
                    </div>
                    {o.hold_id && (
                      <div className="muted mono" style={{ fontSize: 'var(--fs-xs)' }}>
                        Hold {o.hold_id}
                      </div>
                    )}
                    <div className="muted" style={{ fontSize: 'var(--fs-xs)' }}>
                      Placed {new Date(o.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div className="stack-sm" style={{ alignItems: 'flex-end' }}>
                    <div style={{ fontWeight: 700 }}>
                      {formatMoney(o.amount, o.currency)}
                    </div>
                    {o.status === 'placed' && (
                      <Button
                        variant="danger"
                        onClick={() => onCancel(o.id)}
                        loading={cancelling === o.id}
                      >
                        Cancel & refund
                      </Button>
                    )}
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
