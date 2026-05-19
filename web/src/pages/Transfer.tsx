import { FormEvent, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listAccounts, listAccountsForUser } from '@/api/accounts';
import { lookupUserByEmail } from '@/api/auth';
import { ApiError } from '@/api/client';
import { Account, PublicAccount, PublicUser } from '@/api/types';
import { sendTransfer } from '@/api/transfers';
import { AppShell } from '@/components/AppShell';
import { Banner } from '@/components/Banner';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Input } from '@/components/Input';
import { Select } from '@/components/Select';
import { Spinner } from '@/components/Spinner';
import { formatMoney, shortId } from '@/lib/format';

type DestinationMode = 'own' | 'email' | 'uuid';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default function Transfer() {
  const navigate = useNavigate();
  const [accounts, setAccounts] = useState<Account[] | null>(null);
  const [fromId, setFromId] = useState('');

  const [destMode, setDestMode] = useState<DestinationMode>('own');
  const [toOwnId, setToOwnId] = useState('');

  const [recipientEmail, setRecipientEmail] = useState('');
  const [recipient, setRecipient] = useState<PublicUser | null>(null);
  const [recipientAccounts, setRecipientAccounts] = useState<PublicAccount[] | null>(null);
  const [recipientLookupBusy, setRecipientLookupBusy] = useState(false);
  const [recipientError, setRecipientError] = useState<string | null>(null);
  const [recipientAccountId, setRecipientAccountId] = useState('');

  const [uuidInput, setUuidInput] = useState('');

  const [amount, setAmount] = useState('');
  const [purpose, setPurpose] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listAccounts()
      .then((all) => {
        if (cancelled) return;
        const accs = all.filter((a) => !a.closed_at);
        setAccounts(accs);
        if (accs.length > 0) setFromId(accs[0]!.id);
        if (accs.length > 1) setToOwnId(accs[1]!.id);
        else if (accs.length === 1) setDestMode('email');
      })
      .catch((e) => {
        if (cancelled) return;
        setError(e instanceof ApiError ? e.message : 'Could not load your accounts.');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const from = useMemo(() => accounts?.find((a) => a.id === fromId) ?? null, [accounts, fromId]);

  const resetRecipient = () => {
    setRecipient(null);
    setRecipientAccounts(null);
    setRecipientAccountId('');
    setRecipientError(null);
  };

  const lookupRecipient = async () => {
    const email = recipientEmail.trim().toLowerCase();
    if (!email) {
      setRecipientError('Enter the recipient’s email.');
      return;
    }
    setRecipientLookupBusy(true);
    setRecipientError(null);
    setRecipient(null);
    setRecipientAccounts(null);
    setRecipientAccountId('');
    try {
      const user = await lookupUserByEmail(email);
      setRecipient(user);
      const accs = await listAccountsForUser(user.id);
      setRecipientAccounts(accs);
      if (accs.length === 0) {
        setRecipientError('That user has no open accounts to receive money.');
      } else {
        // Prefer an account in the same currency as the source, if any.
        const same = from ? accs.find((a) => a.currency === from.currency) : null;
        setRecipientAccountId((same ?? accs[0]!).id);
      }
    } catch (e) {
      setRecipientError(e instanceof ApiError ? e.message : 'Recipient lookup failed.');
    } finally {
      setRecipientLookupBusy(false);
    }
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!fromId) return setError('Pick a source account.');

    let toId = '';
    if (destMode === 'own') {
      toId = toOwnId;
      if (!toId) return setError('Pick a destination account.');
    } else if (destMode === 'email') {
      if (!recipient) return setError('Look up the recipient first.');
      if (!recipientAccountId) return setError('Pick which of their accounts to credit.');
      toId = recipientAccountId;
    } else {
      toId = uuidInput.trim();
      if (!toId) return setError('Paste an account UUID.');
      if (!UUID_RE.test(toId)) return setError('That does not look like a valid account UUID.');
    }
    if (toId === fromId) return setError('Source and destination accounts must differ.');

    const amt = Number(amount);
    if (Number.isNaN(amt) || amt <= 0) return setError('Enter a positive amount.');
    if (from && amt > from.balance) {
      return setError(`Not enough funds — this account holds ${formatMoney(from.balance, from.currency)}.`);
    }

    setBusy(true);
    try {
      await sendTransfer({
        from_account_id: fromId,
        to_account_id: toId,
        amount: amt,
        purpose: purpose.trim() || undefined,
      });
      setSuccess(
        destMode === 'email' && recipient
          ? `Sent to ${recipient.username}. They'll see it in their activity shortly.`
          : 'Transfer sent. It will show up in your activity shortly.',
      );
      setAmount('');
      setPurpose('');
      const accs = (await listAccounts()).filter((a) => !a.closed_at);
      setAccounts(accs);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Transfer failed.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <AppShell>
      <div className="page-narrow stack" style={{ margin: '0 auto', maxWidth: 560 }}>
        <h1>Send money</h1>
        {accounts === null ? (
          <div className="empty-state">
            <Spinner size="lg" />
          </div>
        ) : accounts.length === 0 ? (
          <Card>
            <div className="stack">
              <Banner tone="info">You need an account before you can send money.</Banner>
              <Button onClick={() => navigate('/accounts/new')}>Open an account</Button>
            </div>
          </Card>
        ) : (
          <Card>
            <form onSubmit={onSubmit} className="stack" noValidate>
              {error && <Banner tone="error">{error}</Banner>}
              {success && <Banner tone="success">{success}</Banner>}

              <Select
                label="From account"
                value={fromId}
                onChange={(e) => setFromId(e.target.value)}
              >
                {accounts.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.currency} — {formatMoney(a.balance, a.currency)}
                  </option>
                ))}
              </Select>

              <div className="field">
                <label>Destination</label>
                <div className="row" style={{ gap: 'var(--space-2)' }}>
                  <Button
                    type="button"
                    variant={destMode === 'own' ? 'primary' : 'secondary'}
                    onClick={() => {
                      setDestMode('own');
                      resetRecipient();
                    }}
                  >
                    My account
                  </Button>
                  <Button
                    type="button"
                    variant={destMode === 'email' ? 'primary' : 'secondary'}
                    onClick={() => setDestMode('email')}
                  >
                    Send to email
                  </Button>
                  <Button
                    type="button"
                    variant={destMode === 'uuid' ? 'primary' : 'secondary'}
                    onClick={() => setDestMode('uuid')}
                  >
                    Account UUID
                  </Button>
                </div>
              </div>

              {destMode === 'own' ? (
                <Select
                  label="To account"
                  value={toOwnId}
                  onChange={(e) => setToOwnId(e.target.value)}
                >
                  <option value="">Select an account</option>
                  {accounts
                    .filter((a) => a.id !== fromId)
                    .map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.currency} — {formatMoney(a.balance, a.currency)}
                      </option>
                    ))}
                </Select>
              ) : destMode === 'uuid' ? (
                <Input
                  label="Recipient account UUID"
                  value={uuidInput}
                  onChange={(e) => setUuidInput(e.target.value)}
                  placeholder="0c9b3f1e-…"
                  hint="The recipient can find this in their dashboard tile."
                  error={
                    uuidInput.trim() && !UUID_RE.test(uuidInput.trim())
                      ? 'Not a valid UUID.'
                      : undefined
                  }
                />
              ) : (
                <div className="stack">
                  <div className="field">
                    <label htmlFor="recipient-email">Recipient email</label>
                    <div className="row" style={{ gap: 'var(--space-2)' }}>
                      <input
                        id="recipient-email"
                        type="email"
                        className="input"
                        value={recipientEmail}
                        onChange={(e) => {
                          setRecipientEmail(e.target.value);
                          if (recipient) resetRecipient();
                        }}
                        placeholder="alice@example.com"
                        autoComplete="off"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            void lookupRecipient();
                          }
                        }}
                      />
                      <Button
                        type="button"
                        variant="secondary"
                        onClick={() => void lookupRecipient()}
                        loading={recipientLookupBusy}
                      >
                        Find
                      </Button>
                    </div>
                    {recipientError && <span className="field-error">{recipientError}</span>}
                  </div>

                  {recipient && recipientAccounts && recipientAccounts.length > 0 && (
                    <>
                      <Banner tone="info">
                        Found <strong>{recipient.username}</strong>. Pick which of their
                        accounts to credit.
                      </Banner>
                      <Select
                        label="Recipient account"
                        value={recipientAccountId}
                        onChange={(e) => setRecipientAccountId(e.target.value)}
                      >
                        {recipientAccounts.map((a) => (
                          <option key={a.id} value={a.id}>
                            {a.currency} — {shortId(a.id)}
                          </option>
                        ))}
                      </Select>
                      {from
                        && recipientAccountId
                        && (() => {
                          const recAcc = recipientAccounts.find((a) => a.id === recipientAccountId);
                          if (!recAcc || recAcc.currency === from.currency) return null;
                          return (
                            <span className="field-hint">
                              Cross-currency: amount will be converted from {from.currency} to {recAcc.currency} at the bank's internal rate.
                            </span>
                          );
                        })()}
                    </>
                  )}
                </div>
              )}

              <Input
                label="Amount"
                type="number"
                step="0.01"
                min="0"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                hint={from ? `Available: ${formatMoney(from.balance, from.currency)}` : undefined}
              />

              <Input
                label="Note (optional)"
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                placeholder="What's it for?"
                maxLength={120}
              />

              <div className="row" style={{ justifyContent: 'flex-end' }}>
                <Button type="button" variant="ghost" onClick={() => navigate(-1)}>
                  Cancel
                </Button>
                <Button type="submit" loading={busy} size="lg">
                  Send transfer
                </Button>
              </div>
            </form>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
