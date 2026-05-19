# 0003 — Tasks

Each task is one PR-sized unit.

1. **Scaffold `web/` Vite + React + TS project.**
   `package.json`, `tsconfig.json`, `vite.config.ts`, `index.html`,
   `src/main.tsx`, `src/App.tsx`. Add `.gitignore` for `node_modules`
   and `dist`.

2. **Design system + base components.**
   `src/styles/tokens.css` (palette, spacing, radii, type),
   `src/styles/globals.css`. Components: `Button`, `Input`, `Select`,
   `Card`, `Banner`, `Spinner`, `Modal`. No external UI library.

3. **API client + auth context + protected route.**
   `src/api/client.ts`, `src/api/auth.ts`, `src/api/accounts.ts`,
   `src/api/transfers.ts`, `src/api/history.ts`,
   `src/auth/AuthContext.tsx`, `src/auth/ProtectedRoute.tsx`.

4. **Pages.**
   `Landing`, `Login`, `Register`, `Dashboard`, `NewAccount`,
   `Transfer`, `History`, `NotFound`. Wired into `App.tsx`'s router.

5. **App shell.**
   `AppShell` component with top bar (logo + user chip + logout) and
   sidebar (Dashboard / Transfer / History / Shop[disabled]). Used by
   all private routes.

6. **Multi-stage Dockerfile + runtime nginx.**
   `web/Dockerfile`, `web/nginx.conf` (SPA fallback, gzip).

7. **Docker-compose + gateway nginx wiring.**
   Add `web` service; drop the static blocks from `nginx/nginx.conf`
   and add `location / { proxy_pass http://web; }`.

8. **Local build verification.**
   `cd web && npm install && npm run build` succeeds with no TS or
   Vite errors.

9. **Update CLAUDE.md / docs.**
   Note the new `web/` project structure in the repository layout
   section. Add a short README to `web/`.
