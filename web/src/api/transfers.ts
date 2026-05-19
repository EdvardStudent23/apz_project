import { requestEnvelope } from './client';
import { Transfer } from './types';

export function sendTransfer(input: {
  from_account_id: string;
  to_account_id: string;
  amount: number;
  purpose?: string;
}) {
  return requestEnvelope<Transfer>('/transfers', {
    method: 'POST',
    body: input,
  });
}
