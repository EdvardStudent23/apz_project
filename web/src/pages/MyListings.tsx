import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ApiError } from '@/api/client';
import { listMyProducts } from '@/api/shop';
import { Product } from '@/api/types';
import { AppShell } from '@/components/AppShell';
import { Banner } from '@/components/Banner';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Spinner } from '@/components/Spinner';
import { formatMoney } from '@/lib/format';

function StatusBadge({ status }: { status: Product['status'] }) {
  const tone =
    status === 'approved' ? 'banner-success'
    : status === 'rejected' ? 'banner-error'
    : 'banner-warn';
  return (
    <span className={`banner ${tone}`} style={{ padding: '2px 8px', borderRadius: 999, fontSize: 12 }}>
      {status}
    </span>
  );
}

interface LocationState {
  justListed?: boolean;
}

export default function MyListings() {
  const [products, setProducts] = useState<Product[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const location = useLocation();
  const justListed = (location.state as LocationState | null)?.justListed;

  useEffect(() => {
    let cancelled = false;
    listMyProducts()
      .then((ps) => {
        if (!cancelled) setProducts(ps);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof ApiError ? e.message : 'Could not load your listings.');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <AppShell>
      <div className="stack" style={{ gap: 'var(--space-6)' }}>
        <div className="row-between">
          <h1>My listings</h1>
          <Link to="/shop/new">
            <Button>+ New listing</Button>
          </Link>
        </div>

        {justListed && (
          <Banner tone="success">
            Submitted for review. An admin will approve or reject your listing shortly.
          </Banner>
        )}
        {error && <Banner tone="error">{error}</Banner>}

        {products === null ? (
          <div className="empty-state"><Spinner size="lg" /></div>
        ) : products.length === 0 ? (
          <div className="empty-state">You haven't listed anything yet.</div>
        ) : (
          <div className="stack">
            {products.map((p) => (
              <Card key={p.id}>
                <div className="row-between" style={{ alignItems: 'flex-start' }}>
                  <div className="stack-sm" style={{ flex: 1 }}>
                    <div className="row" style={{ gap: 'var(--space-3)' }}>
                      <h3 style={{ margin: 0 }}>{p.name}</h3>
                      <StatusBadge status={p.status} />
                    </div>
                    {p.description && <div className="muted">{p.description}</div>}
                    {p.moderation_note && (
                      <div className="muted" style={{ fontSize: 'var(--fs-xs)' }}>
                        Moderator note: <em>{p.moderation_note}</em>
                      </div>
                    )}
                  </div>
                  <div style={{ fontWeight: 700 }}>
                    {formatMoney(p.price, p.currency)}
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
