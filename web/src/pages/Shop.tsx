import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listAccounts } from '@/api/accounts';
import { ApiError } from '@/api/client';
import { listApprovedProducts, placeOrder } from '@/api/shop';
import { Account, Product } from '@/api/types';
import { AppShell } from '@/components/AppShell';
import { Banner } from '@/components/Banner';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Modal } from '@/components/Modal';
import { Select } from '@/components/Select';
import { Spinner } from '@/components/Spinner';
import { formatMoney } from '@/lib/format';

export default function Shop() {
  const navigate = useNavigate();
  const [products, setProducts] = useState<Product[] | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [buyTarget, setBuyTarget] = useState<Product | null>(null);
  const [buyAccountId, setBuyAccountId] = useState<string>('');
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [ps, allAccs] = await Promise.all([listApprovedProducts(), listAccounts()]);
      const accs = allAccs.filter((a) => !a.closed_at);
      setProducts(ps);
      setAccounts(accs);
      if (accs.length > 0 && !buyAccountId) setBuyAccountId(accs[0]!.id);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not load the shop.');
    }
  }, [buyAccountId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const openBuy = (product: Product) => {
    setBuyTarget(product);
    setError(null);
    setSuccess(null);
  };
  const closeBuy = () => {
    if (!busy) setBuyTarget(null);
  };

  const confirmBuy = async () => {
    if (!buyTarget || !buyAccountId) return;
    setBusy(true);
    setError(null);
    try {
      await placeOrder(buyTarget.id, buyAccountId);
      setBuyTarget(null);
      setSuccess('Order placed. Funds are now held on your account.');
      void refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not place the order.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <AppShell>
      <div className="stack" style={{ gap: 'var(--space-6)' }}>
        <div className="row-between">
          <div>
            <h1 style={{ marginBottom: 4 }}>Shop</h1>
            <p className="muted" style={{ margin: 0 }}>
              Browse listings from other NanoBank members. Paying for an order
              freezes the price on your account until the order is fulfilled.
            </p>
          </div>
          <div className="row">
            <Link to="/shop/orders">
              <Button variant="ghost">My orders</Button>
            </Link>
            <Button variant="primary" onClick={() => navigate('/shop/new')}>
              Sell something
            </Button>
          </div>
        </div>

        {error && <Banner tone="error">{error}</Banner>}
        {success && <Banner tone="success">{success}</Banner>}

        {products === null ? (
          <div className="empty-state">
            <Spinner size="lg" />
          </div>
        ) : products.length === 0 ? (
          <div className="empty-state">
            Nothing for sale right now. Be the first — <Link to="/shop/new">list a product</Link>.
          </div>
        ) : (
          <div className="account-grid">
            {products.map((p) => (
              <Card key={p.id}>
                <div className="stack-sm">
                  <h3 style={{ margin: 0 }}>{p.name}</h3>
                  <div className="muted" style={{ fontSize: 'var(--fs-sm)' }}>
                    {p.description || 'No description.'}
                  </div>
                  <div
                    style={{
                      fontSize: 'var(--fs-2xl)',
                      fontWeight: 700,
                      letterSpacing: '-0.01em',
                    }}
                  >
                    {formatMoney(p.price, p.currency)}
                  </div>
                  <Button onClick={() => openBuy(p)}>Buy now</Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      <Modal open={buyTarget !== null} onClose={closeBuy} title="Confirm purchase">
        {buyTarget && (
          <div className="stack">
            <p className="muted" style={{ margin: 0 }}>
              You're about to order:
            </p>
            <Card tight>
              <div className="row-between">
                <strong>{buyTarget.name}</strong>
                <span>{formatMoney(buyTarget.price, buyTarget.currency)}</span>
              </div>
            </Card>

            {accounts.length === 0 ? (
              <Banner tone="warn">
                You need an account to make purchases.{' '}
                <Link to="/accounts/new">Open one first</Link>.
              </Banner>
            ) : (
              <Select
                label="Pay from"
                value={buyAccountId}
                onChange={(e) => setBuyAccountId(e.target.value)}
              >
                {accounts.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.currency} — {formatMoney(a.balance, a.currency)}
                  </option>
                ))}
              </Select>
            )}

            <Banner tone="info">
              Confirming places a hold on your account for {formatMoney(buyTarget.price, buyTarget.currency)} (converted if your account currency differs).
              The money stays in your account but cannot be spent until the order is fulfilled or cancelled.
            </Banner>

            <div className="row" style={{ justifyContent: 'flex-end' }}>
              <Button variant="ghost" onClick={closeBuy} disabled={busy}>
                Cancel
              </Button>
              <Button
                onClick={confirmBuy}
                loading={busy}
                disabled={!buyAccountId || accounts.length === 0}
              >
                Place order
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </AppShell>
  );
}

