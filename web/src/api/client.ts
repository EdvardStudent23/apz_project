import { ApiEnvelope } from './types';

const TOKEN_KEY = 'nanobank.token';
const USER_KEY = 'nanobank.user';

export type ErrorKind =
  | 'network'           // browser couldn't reach the gateway at all
  | 'service_unavailable' // gateway returned 502/503/504 — backend down
  | 'server'            // 500 — internal error in a backend service
  | 'auth'              // 401 — token gone / expired
  | 'forbidden'         // 403 — admin / ownership check
  | 'not_found'         // 404
  | 'conflict'          // 409 — domain validation (insufficient funds etc.)
  | 'client'            // any other 4xx
  | 'envelope';         // ApiResponse(status=false)

export class ApiError extends Error {
  status: number;
  body: unknown;
  kind: ErrorKind;
  /** True for any failure mode that means "back-end isn't healthy right now"
   * — used by the UI to show a graceful "we're investigating" message instead
   * of a raw 500 / 502 / network error. */
  serviceUnavailable: boolean;

  constructor(message: string, status: number, body: unknown, kind: ErrorKind) {
    super(message);
    this.status = status;
    this.body = body;
    this.kind = kind;
    this.serviceUnavailable =
      kind === 'network' || kind === 'service_unavailable' || kind === 'server';
    this.name = 'ApiError';
  }
}

// ── Friendly messages for the user ──────────────────────────────────────

const SERVICE_DOWN_MSG =
  "Some services are temporarily unavailable. We're investigating — your account and balances are safe. Please try again in a moment.";

const NETWORK_DOWN_MSG =
  "Can't reach NanoBank right now. Some services may be down — please wait while we investigate.";

const SERVER_ERROR_MSG =
  "Something went wrong on our side. We're looking into it — please try again shortly.";

// ── Tiny pub-sub for live health monitoring ────────────────────────────

type HealthListener = (event: 'success' | 'fail', err?: ApiError) => void;
const healthListeners = new Set<HealthListener>();
export function subscribeApiHealth(listener: HealthListener): () => void {
  healthListeners.add(listener);
  return () => healthListeners.delete(listener);
}
function emitHealth(event: 'success' | 'fail', err?: ApiError) {
  for (const l of healthListeners) {
    try {
      l(event, err);
    } catch {
      /* swallow listener errors */
    }
  }
}

// ── Unauthorized handler ───────────────────────────────────────────────

type Unauthorized = () => void;
let onUnauthorized: Unauthorized = () => {};
export function setUnauthorizedHandler(handler: Unauthorized) {
  onUnauthorized = handler;
}

// ── Token / user storage ───────────────────────────────────────────────

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function storeToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
export function storeUser<T>(user: T) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}
export function getStoredUser<T>(): T | null {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  query?: Record<string, string | number | undefined>;
  auth?: boolean;
}

function buildUrl(path: string, query?: RequestOptions['query']): string {
  if (!query) return path;
  const entries = Object.entries(query).filter(([, v]) => v !== undefined && v !== '');
  if (entries.length === 0) return path;
  const params = new URLSearchParams();
  for (const [k, v] of entries) params.set(k, String(v));
  return `${path}?${params.toString()}`;
}

function extractErrorMessage(body: unknown, fallback: string): string {
  if (!body || typeof body !== 'object') return fallback;
  const obj = body as Record<string, unknown>;

  if (typeof obj.detail === 'string') return obj.detail;
  if (Array.isArray(obj.detail)) {
    const msgs = obj.detail
      .map((d) =>
        typeof d === 'object' && d && 'msg' in d ? String((d as { msg: unknown }).msg) : null,
      )
      .filter(Boolean);
    if (msgs.length > 0) return msgs.join('; ');
  }

  if (typeof obj.response === 'string') return obj.response;
  if (obj.response && typeof obj.response === 'object' && 'message' in obj.response) {
    return String((obj.response as { message: unknown }).message);
  }
  if (typeof obj.message === 'string') return obj.message;
  return fallback;
}

function kindFromStatus(status: number): ErrorKind {
  if (status === 0) return 'network';
  if (status === 401) return 'auth';
  if (status === 403) return 'forbidden';
  if (status === 404) return 'not_found';
  if (status === 409) return 'conflict';
  if (status >= 400 && status < 500) return 'client';
  if (status === 502 || status === 503 || status === 504) return 'service_unavailable';
  if (status >= 500) return 'server';
  return 'client';
}

function friendlyMessageFor(
  kind: ErrorKind,
  rawMessage: string,
  status: number,
): string {
  // For backend "service down" categories, override whatever the backend (or
  // nginx) said with a calm, course-defense-friendly message. The exact body
  // is still available on `err.body` for debugging.
  switch (kind) {
    case 'network':
      return NETWORK_DOWN_MSG;
    case 'service_unavailable':
      return SERVICE_DOWN_MSG;
    case 'server':
      return SERVER_ERROR_MSG;
    case 'auth':
      return 'Your session has expired. Please sign in again.';
    default:
      // Domain/validation errors keep the backend's specific message so the
      // user knows what to do (e.g., "Insufficient funds").
      return rawMessage || `Request failed (${status})`;
  }
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, query, auth = true } = opts;

  const headers: Record<string, string> = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth) {
    const token = getStoredToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (e) {
    const err = new ApiError(NETWORK_DOWN_MSG, 0, e, 'network');
    emitHealth('fail', err);
    throw err;
  }

  let parsed: unknown = null;
  const text = await response.text();
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      // Non-JSON bodies (e.g., nginx's HTML 502 page) are kept as-is on
      // err.body but never shown to the user — the friendly message wins.
      parsed = text;
    }
  }

  if (response.status === 401 && auth) {
    onUnauthorized();
    const err = new ApiError(friendlyMessageFor('auth', '', 401), 401, parsed, 'auth');
    // 401 isn't a service-down event; don't pollute the health monitor.
    emitHealth('success');
    throw err;
  }

  if (!response.ok) {
    const kind = kindFromStatus(response.status);
    const rawMessage = extractErrorMessage(parsed, `Request failed (${response.status})`);
    const friendly = friendlyMessageFor(kind, rawMessage, response.status);
    const err = new ApiError(friendly, response.status, parsed, kind);
    emitHealth(err.serviceUnavailable ? 'fail' : 'success', err);
    throw err;
  }

  emitHealth('success');
  return parsed as T;
}

export async function requestEnvelope<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const env = await request<ApiEnvelope<T>>(path, opts);
  if (typeof env === 'object' && env !== null && 'status' in env) {
    if (!env.status) {
      const msg = typeof env.response === 'string' ? env.response : 'Request failed';
      throw new ApiError(msg, 200, env, 'envelope');
    }
    return env.response;
  }
  return env as unknown as T;
}
