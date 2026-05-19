import { Account } from '@/api/types';
import { formatMoney } from '@/lib/format';
import { Button } from './Button';

interface Props {
  account: Account;
  onClick?: () => void;
  onClose?: () => void;
  closing?: boolean;
}

export function AccountTile({ account, onClick, onClose, closing }: Props) {
  const isClosed = Boolean(account.closed_at);
  const held = Number(account.held_balance ?? 0);
  const available = Number(account.available_balance ?? account.balance);
  const canClose = !isClosed && Number(account.balance) === 0 && held === 0;
  return (
    <div
      className="account-tile"
      role={onClick && !isClosed ? 'button' : undefined}
      tabIndex={onClick && !isClosed ? 0 : undefined}
      onClick={isClosed ? undefined : onClick}
      onKeyDown={(e) => {
        if (onClick && !isClosed && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onClick();
        }
      }}
      style={{
        cursor: onClick && !isClosed ? 'pointer' : undefined,
        opacity: isClosed ? 0.6 : undefined,
      }}
    >
      <div className="account-tile-header">
        <span className="account-tile-currency">{account.currency}</span>
        <span className="text-soft" style={{ fontSize: 'var(--fs-xs)' }}>
          {isClosed
            ? `Closed ${new Date(account.closed_at!).toLocaleDateString()}`
            : `Opened ${new Date(account.created_at).toLocaleDateString()}`}
        </span>
      </div>
      <div className="account-tile-balance" style={isClosed ? { textDecoration: 'line-through' } : undefined}>
        {formatMoney(account.balance, account.currency)}
      </div>
      {held > 0 && !isClosed && (
        <div
          className="banner banner-warn"
          style={{ padding: '4px 8px', fontSize: 'var(--fs-xs)', gap: 4 }}
          title="Funds held for pending orders or holds"
        >
          <span>
            🔒 {formatMoney(held, account.currency)} held · available{' '}
            <strong>{formatMoney(available, account.currency)}</strong>
          </span>
        </div>
      )}
      <div className="account-tile-id" title={account.id}>
        {account.id}
      </div>
      {onClose && !isClosed && (
        <div style={{ marginTop: 'var(--space-2)' }}>
          <Button
            variant="ghost"
            onClick={(e) => {
              e.stopPropagation();
              onClose();
            }}
            disabled={!canClose}
            loading={closing}
            title={
              canClose
                ? 'Close this account'
                : 'Transfer the remaining balance and release any holds before closing'
            }
          >
            Close account
          </Button>
        </div>
      )}
    </div>
  );
}

export function AddAccountTile({ onClick }: { onClick: () => void }) {
  return (
    <button type="button" className="account-tile account-tile-add" onClick={onClick}>
      + Open another account
    </button>
  );
}
