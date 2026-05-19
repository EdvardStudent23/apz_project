# 0003 — Plan: bank UI redesign

## Affected components

- **New service:** `web` container, multi-stage Dockerfile
  (`node:20-alpine` → `nginx:1.27-alpine`). Joins `bank_net`. No
  exposed host port — only the gateway reaches it.
- **Gateway nginx (`nginx/nginx.conf`):** the static-file blocks for
  `/` and `/web/` are removed; a single `location / { proxy_pass
  http://web; }` block routes the SPA. All `/auth/*`, `/accounts`,
  `/transfers`, `/history`, `/.well-known/*`, `/market/*` blocks
  stay untouched.
- **`docker-compose.yml`:** add `web` service; the `nginx` service no
  longer mounts `./web`.
- **`web/`:** becomes a Vite + React + TypeScript project. Source under
  `web/src`. Build output under `web/dist` (gitignored).

## Tech choices

- React 18, TypeScript, Vite, React Router v6
- `clsx` for class composition; **no** component library
- Hand-rolled CSS using design tokens (custom properties)
- State: built-in `useState` + a single `AuthContext`
- API access: a thin `fetch` wrapper in `src/api/client.ts` that
  injects `Authorization: Bearer <token>` and routes `401` through a
  central handler that logs out + redirects
- Token storage: `localStorage` (single key `nanobank.token`); user
  profile cached alongside under `nanobank.user`

## Data flow

- Login: `POST /auth/login` returns `{ user, tokens }`. Persist
  `tokens.access_token` and `user` to `localStorage`, set them on the
  `AuthContext`. Future requests include the bearer header.
- Refresh on page reload: `AuthContext` hydrates from `localStorage`
  during initialisation. Optionally calls `GET /auth/me` to validate
  the token; failure clears storage.
- Logout: `POST /auth/logout` (best-effort — fire and forget if it
  errors), clear storage, route to `/login`.
- All other API responses use the project's `ApiResponse` envelope
  (`{ status, response }`); the client unwraps successes and throws
  a typed `ApiError` for failures so pages get a clean message via
  `try / catch`.

## SPA routing

- React Router with `BrowserRouter`. Nginx in the `web` container
  has `try_files $uri /index.html;` so deep links work.
- `<ProtectedRoute>` wraps `/dashboard`, `/accounts/new`, `/transfer`,
  `/history`. While unauth, redirects to `/login?next=<path>`.
- After login, if `?next=` is present and starts with `/`, redirect
  there; otherwise to `/dashboard`.

## Schemas the UI relies on

```ts
// Auth
type User = { id: number; username: string; email: string; is_active: boolean; created_at: string };
type Tokens = { access_token: string; refresh_token: string; token_type: string; expires_at: string };
type AuthResponse = { user: User; tokens: Tokens };

// Accounts
type Account = { id: string; currency: 'USD' | 'EUR' | 'UAH'; balance: number; created_at: string };

// Transfers
type Transfer = {
  id: string;
  sender_account_id: string;
  receiver_account_id: string;
  amount: number;
  currency: string;
  purpose: string | null;
  created_at: string;
};
type TransferRequest = {
  from_account_id: string;
  to_account_id: string;
  amount: number;
  purpose?: string;
};

// History
type HistoryEntry = {
  sender_id: string;
  receiver_id: string;
  amount: number;
  currency: string;
  type: string;
  timestamp: string;
};
```

## Migration / rollout

- Old `web/*.md` demo guides and `web/index.html` move to
  `docs/legacy/web-demo/` so git history is preserved without
  cluttering the new SPA root.
- `nginx/nginx.conf` change is backwards-incompatible (drops static
  block) but coordinated with the same PR that adds the `web`
  service — `make up` brings up the whole stack in lockstep.
- No database migrations.
- No event-schema changes.

## Risks

- **Build time in CI.** `npm ci` adds ~30–60s. Acceptable.
- **Token in localStorage** is XSS-readable. For a course demo this
  is acceptable; documented in the spec as not production-hardened.
- **Account UUIDs are long.** UX risk on the Transfer screen — we
  offer a dropdown for own-accounts plus a paste field for external
  ones.
