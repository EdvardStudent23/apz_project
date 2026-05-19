# 0003 — Bank UI redesign

## Why

The current `web/index.html` is a single dashboard that exposes every
service call and an API inspector on one page. It looks like a developer
demo, not a bank. The course brief asks for a usable end-user
experience; this spec replaces the demo page with a real-feeling
online-banking SPA.

## In scope

A multi-screen single-page application served at `/` through the
existing Nginx gateway, covering the user-facing flow:

1. **Landing** — public welcome screen with sign-in / register CTAs.
2. **Register** — collect `username`, `email`, `password`, call
   `POST /auth/register`, redirect to `/login` with a success banner.
3. **Login** — collect `username`, `password`, call `POST /auth/login`,
   persist the access token, redirect to `/dashboard`.
4. **Dashboard** — show all of the user's accounts as cards (balance +
   currency), a "Send money" CTA, and a recent-activity preview
   (last 5 transactions).
5. **Open account** — modal/screen to create a new account by picking
   a currency (USD/EUR/UAH). Calls `POST /accounts` with
   `initial_balance: 1000`.
6. **Transfer** — pick a source account from a dropdown, paste or
   select a destination account, enter an amount, optionally a
   purpose. Calls `POST /transfers`. Shows success or a clear error.
7. **History** — full transaction list. Filter by account; date is
   shown per row; amount and currency are visible.
8. **Logout** — clears the local token and calls `POST /auth/logout`.

The UI talks only to endpoints behind the Nginx gateway on the same
origin (relative URLs). No CORS work required.

## Out of scope

- **BankMarket / Shop** — the BankMarket service currently has no
  routes. The UI shows a disabled "Shop — coming soon" item in the
  navigation; the actual screen is deferred to its own spec once the
  BankMarket API exists.
- **Refresh-token rotation** — the access token's 30-minute lifetime
  is fine for a demo. On `401` the UI logs the user out and sends
  them to `/login`.
- **Production hardening** — no PWA, no service worker, no analytics.
- **Account-to-account look-up by username** — destination is entered
  by account UUID, picked from the user's own accounts, or pasted
  from a known recipient.

## Acceptance criteria

- Opening `http://localhost:8080/` (after `make up`) loads the
  redesigned landing page.
- A user can register, then log in, then create two accounts, then
  transfer between them, then see the transfer in history — all
  without seeing raw JSON or a developer-style inspector.
- Refreshing the page while logged in keeps the user logged in.
- A direct URL like `/transfer` while logged out redirects to
  `/login`, and after a successful login bounces back to `/transfer`.
- Calling a backend endpoint that returns `401` logs the user out
  and routes them to `/login` with an explanatory banner.
- The build runs entirely inside `docker compose build` — graders do
  not need Node installed locally.
- `pyright` / `ruff` are unaffected (no Python changed).

## Visual style

Clean modern fintech: white background, dark text, one accent colour
(violet/blue gradient already used in the legacy page is kept as the
accent token so screenshots in older course materials stay coherent).
Cards are white with soft shadows and 12px corner radius. Type is
system sans. Layout is a left sidebar + top bar on desktop, collapsing
to a hamburger drawer on narrow viewports.

## Non-functional

- First contentful paint under 1s on a warm cache (small bundle —
  React + Router only, no UI library).
- All inputs have labels; all interactive elements are reachable by
  keyboard; focus states visible.
- No PII in logs from the browser console.
