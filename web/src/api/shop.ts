import { requestEnvelope } from './client';
import { Currency, Order, Product } from './types';

export function listApprovedProducts() {
  return requestEnvelope<Product[]>('/market/products');
}

export function listMyProducts() {
  return requestEnvelope<Product[]>('/market/products/mine');
}

export function listPendingProducts() {
  return requestEnvelope<Product[]>('/market/products/pending');
}

export function createProduct(input: {
  name: string;
  description: string;
  price: number;
  currency: Currency;
}) {
  return requestEnvelope<Product>('/market/products', {
    method: 'POST',
    body: input,
  });
}

export function moderateProduct(
  productId: string,
  decision: 'approved' | 'rejected',
  note?: string,
) {
  return requestEnvelope<Product>(`/market/products/${productId}/moderate`, {
    method: 'POST',
    body: { decision, note: note ?? null },
  });
}

export function placeOrder(productId: string, accountId: string) {
  return requestEnvelope<Order>('/market/orders', {
    method: 'POST',
    body: { product_id: productId, account_id: accountId },
  });
}

export function listMyOrders() {
  return requestEnvelope<Order[]>('/market/orders/mine');
}

export function cancelOrder(orderId: string) {
  return requestEnvelope<Order>(`/market/orders/${orderId}/cancel`, {
    method: 'POST',
  });
}
