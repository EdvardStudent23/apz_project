import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createAccount } from '@/api/accounts';
import { ApiError } from '@/api/client';
import { Currency } from '@/api/types';
import { AppShell } from '@/components/AppShell';
import { Banner } from '@/components/Banner';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Input } from '@/components/Input';
import { Select } from '@/components/Select';

export default function NewAccount() {
  const navigate = useNavigate();
  const [currency, setCurrency] = useState<Currency>('USD');
  const [initialBalance, setInitialBalance] = useState<string>('1000');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    const amount = Number(initialBalance);
    if (Number.isNaN(amount) || amount < 0) {
      setError('Initial balance must be a non-negative number.');
      return;
    }
    setBusy(true);
    try {
      await createAccount(currency, amount);
      navigate('/dashboard', { replace: true });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Could not create the account.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <AppShell>
      <div className="page-narrow stack" style={{ margin: '0 auto' }}>
        <h1>Open a new account</h1>
        <Card>
          <form onSubmit={onSubmit} className="stack" noValidate>
            {error && <Banner tone="error">{error}</Banner>}
            <Select
              label="Currency"
              value={currency}
              onChange={(e) => setCurrency(e.target.value as Currency)}
            >
              <option value="USD">USD — US Dollar</option>
              <option value="EUR">EUR — Euro</option>
              <option value="UAH">UAH — Ukrainian hryvnia</option>
            </Select>
            <Input
              label="Initial balance"
              type="number"
              step="0.01"
              min="0"
              value={initialBalance}
              onChange={(e) => setInitialBalance(e.target.value)}
              hint="Demo accounts start with a small balance so you can try transfers right away."
            />
            <div className="row" style={{ justifyContent: 'flex-end' }}>
              <Button type="button" variant="ghost" onClick={() => navigate(-1)}>
                Cancel
              </Button>
              <Button type="submit" loading={busy}>
                Open account
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </AppShell>
  );
}
