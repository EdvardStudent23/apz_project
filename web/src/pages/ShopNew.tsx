import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ApiError } from '@/api/client';
import { createProduct } from '@/api/shop';
import { Currency } from '@/api/types';
import { AppShell } from '@/components/AppShell';
import { Banner } from '@/components/Banner';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Input } from '@/components/Input';
import { Select } from '@/components/Select';

export default function ShopNew() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [currency, setCurrency] = useState<Currency>('USD');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    const priceNum = Number(price);
    if (name.trim().length < 2) return setError('Name must be at least 2 characters.');
    if (Number.isNaN(priceNum) || priceNum <= 0) return setError('Price must be a positive number.');

    setBusy(true);
    try {
      await createProduct({
        name: name.trim(),
        description: description.trim(),
        price: priceNum,
        currency,
      });
      navigate('/shop/mine', {
        replace: true,
        state: { justListed: true },
      });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not create the listing.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <AppShell>
      <div className="page-narrow stack" style={{ margin: '0 auto', maxWidth: 560 }}>
        <h1>List a product</h1>
        <Card>
          <form onSubmit={onSubmit} className="stack" noValidate>
            {error && <Banner tone="error">{error}</Banner>}
            <Banner tone="info">
              After you publish, an admin reviews and approves your listing before it goes on sale.
            </Banner>
            <Input
              label="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Vintage espresso machine"
              maxLength={120}
              autoFocus
            />
            <div className="field">
              <label htmlFor="prod-desc">Description</label>
              <textarea
                id="prod-desc"
                className="input"
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional — describe what you're selling, condition, etc."
                maxLength={2000}
                style={{ resize: 'vertical' }}
              />
            </div>
            <Input
              label="Price"
              type="number"
              step="0.01"
              min="0"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="0.00"
            />
            <Select
              label="Currency"
              value={currency}
              onChange={(e) => setCurrency(e.target.value as Currency)}
            >
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="UAH">UAH</option>
            </Select>
            <div className="row" style={{ justifyContent: 'flex-end' }}>
              <Button type="button" variant="ghost" onClick={() => navigate(-1)}>
                Cancel
              </Button>
              <Button type="submit" loading={busy}>
                Submit for review
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </AppShell>
  );
}
