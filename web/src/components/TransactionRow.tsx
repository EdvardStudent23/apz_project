import { HistoryEntry } from '@/api/types';
import { formatMoney } from '@/lib/format';

interface Props {
  entry: HistoryEntry;
  perspective: 'in' | 'out';
}

export function TransactionRow({ entry, perspective }: Props) {
  const isOut = perspective === 'out';
  const counterparty = isOut ? entry.receiver_id : entry.sender_id;
  const sign = isOut ? '−' : '+';
  return (
    <div className="txn-row">
      <div className={`txn-icon ${isOut ? 'txn-icon-out' : 'txn-icon-in'}`}>{isOut ? '↑' : '↓'}</div>
      <div className="txn-meta">
        <div className="txn-title">{isOut ? 'Sent' : 'Received'}</div>
        <div className="txn-sub" title={counterparty}>
          {isOut ? 'To' : 'From'} {counterparty}
        </div>
        <div className="txn-sub">{new Date(entry.timestamp).toLocaleString()}</div>
      </div>
      <div className={`txn-amount ${isOut ? 'txn-amount-out' : 'txn-amount-in'}`}>
        {sign}
        {formatMoney(entry.amount, entry.currency)}
      </div>
    </div>
  );
}
