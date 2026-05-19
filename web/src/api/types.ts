export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_admin?: boolean;
  created_at: string;
}

export interface PublicUser {
  id: number;
  username: string;
}

export interface PublicAccount {
  id: string;
  currency: Currency;
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_at: string;
}

export interface AuthResponse {
  user: User;
  tokens: Tokens;
}

export type Currency = 'USD' | 'EUR' | 'UAH';

export interface Account {
  id: string;
  currency: Currency;
  balance: number;
  held_balance?: number;
  available_balance?: number;
  created_at: string;
  closed_at?: string | null;
}

export type ProductStatus = 'pending' | 'approved' | 'rejected';

export interface Product {
  id: string;
  owner_id: string;
  name: string;
  description: string;
  price: number;
  currency: Currency;
  status: ProductStatus;
  moderation_note: string | null;
  created_at: string;
}

export type OrderStatus = 'placed' | 'cancelled';

export interface Order {
  id: string;
  product_id: string;
  buyer_id: string;
  hold_id: string | null;
  amount: number;
  currency: string;
  status: OrderStatus;
  created_at: string;
}

export interface Transfer {
  id: string;
  sender_account_id: string;
  receiver_account_id: string;
  amount: number;
  currency: string;
  purpose: string | null;
  created_at: string;
}

export interface HistoryEntry {
  sender_id: string;
  receiver_id: string;
  amount: number;
  currency: string;
  type: string;
  timestamp: string;
}

export interface ApiEnvelope<T> {
  status: boolean;
  response: T;
}
