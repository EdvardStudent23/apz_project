import { request } from './client';
import { AuthResponse, PublicUser, User } from './types';

export function register(input: { username: string; email: string; password: string }) {
  return request<AuthResponse>('/auth/register', {
    method: 'POST',
    body: input,
    auth: false,
  });
}

export function login(input: { username: string; password: string }) {
  return request<AuthResponse>('/auth/login', {
    method: 'POST',
    body: input,
    auth: false,
  });
}

export function logout() {
  return request<{ message: string }>('/auth/logout', { method: 'POST' });
}

export function me() {
  return request<User>('/auth/me');
}

export function lookupUserByEmail(email: string) {
  return request<PublicUser>('/auth/users/lookup', { query: { email } });
}

export function lookupUserByUsername(username: string) {
  return request<PublicUser>('/auth/users/lookup', { query: { username } });
}
