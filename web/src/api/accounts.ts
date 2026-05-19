import { requestEnvelope } from './client';
import { Account, Currency, PublicAccount } from './types';

export function listAccounts() {
  return requestEnvelope<Account[]>('/accounts');
}

export function listAccountsForUser(userId: number | string) {
  return requestEnvelope<PublicAccount[]>(`/accounts/by-user/${userId}`);
}

export function createAccount(currency: Currency, initialBalance = 1000) {
  return requestEnvelope<Account>('/accounts', {
    method: 'POST',
    body: { currency, initial_balance: initialBalance },
  });
}

export function closeAccount(accountId: string) {
  return requestEnvelope<Account>(`/accounts/${accountId}/close`, {
    method: 'POST',
  });
}
