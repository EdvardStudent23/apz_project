# NanoBank Web

React + TypeScript + Vite single-page app that fronts the NanoBank
microservices.

## Local development

```bash
cd web
npm install
npm run dev              # http://localhost:5173 — proxies API to :8080
```

Vite's dev server proxies `/auth`, `/accounts`, `/transfers`,
`/history`, `/.well-known`, and `/market` to `http://localhost:8080`
(the NanoBank gateway). Override with `VITE_GATEWAY_URL=...` if your
gateway lives elsewhere.

Backend must be running:

```bash
make up           # from repo root
```

## Production build

```bash
npm run build     # produces ./dist
```

In Docker:

```bash
docker compose build web
docker compose up -d web
```

The gateway (`nginx` service) proxies any non-API path to this `web`
container. Visit `http://localhost:8080/`.

## Layout

- `src/api/` — typed API client; `client.ts` wraps `fetch`, handles
  401s globally
- `src/auth/` — `AuthContext`, `ProtectedRoute`
- `src/components/` — reusable UI primitives + bank-specific tiles/rows
- `src/pages/` — one file per screen
- `src/styles/` — design tokens + globals (CSS variables)
- `src/lib/` — small utilities (`formatMoney`, `initials`, …)

## Notes

- Token lives in `localStorage` under `nanobank.token`. Cleared on
  logout or on any backend `401`.
- BankMarket service has no public API yet — the **Shop** nav item is
  intentionally disabled.
- Spec for this UI: `specs/0003-bank-ui-redesign/`.
