import { requestEnvelope } from './client';
import { HistoryEntry } from './types';

export function listHistoryByUser(userId: number | string) {
  return requestEnvelope<HistoryEntry[]>('/history', {
    query: { user_id: String(userId) },
  });
}

export function listHistoryByAccount(accountId: string) {
  return requestEnvelope<HistoryEntry[]>('/history', {
    query: { account_id: accountId },
  });
}
