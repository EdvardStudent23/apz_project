# Plan: DevOps Infrastructure & API Gateway

**Spec:** [spec.md](spec.md)

---

## Affected files

| File | Action | Notes |
|------|--------|-------|
| `infrastructure/Dockerfile.base` | Create | Python 3.13-slim + uv; used as build base |
| `services/auth/Dockerfile` | Replace | Rewrite to uv monorepo pattern (build context = repo root) |
| `services/core_banking/Dockerfile` | Create | Same pattern |
| `services/history/Dockerfile` | Replace | Same pattern |
| `services/bankmarket/Dockerfile` | Create | Same pattern |
| `nginx/nginx.conf` | Create | Upstream `auth` (least_conn, 2 servers); path-based routing |
| `docker-compose.yml` | Create | Canonical root-level compose file |
| `infrastructure/github-actions/ci.yml` | Create | Lint + type-check + test + build |
| `Makefile` | Update | Replace TODO stubs with real `docker compose` invocations |

## Key decisions

### Build context = repo root
All service Dockerfiles use `.` as their build context so they can `COPY libs/`
and the workspace `pyproject.toml`. The `docker-compose.yml` specifies
`context: .` and `dockerfile: services/<name>/Dockerfile` for each service.

### uv for dependency installation
Each Dockerfile copies the workspace `pyproject.toml` + `uv.lock*`, then all
`libs/` sources, then its own `services/<name>/` source, and runs
`uv sync --package <name> --no-dev`. The resulting `.venv` is what runs the
service. No `requirements.txt` needed.

### Nginx routing strategy
- `/auth/` → `upstream auth` (least\_conn over `auth_1:8001`, `auth_2:8001`)
- `/.well-known/` → `upstream auth` (JWKS endpoint)
- `/accounts`, `/transfers` → `core_banking:8000`
- `/history` → `history:8000`
- `/market/` → `bankmarket:8000`
- All locations forward `X-Request-Id`, `X-Forwarded-For`, and
  `Authorization` headers unchanged.

### MongoDB replica-set bootstrap
A one-shot `mongo_init` service depends on all three mongo nodes reaching
healthy state, then calls `rs.initiate(...)` via `mongosh`. `restart: "no"`
ensures it does not loop.

### Environment variables
Secrets (passwords, JWT key) are defined inline in `docker-compose.yml`
with obvious placeholder values. Developers override them via a root `.env`
file (listed in `.gitignore`). No defaults are hardcoded in application code.

### GitHub Actions strategy
Single workflow `ci.yml`:
- Trigger: `push` to `main`, `pull_request` targeting `main`
- Job `lint-and-test`: installs uv, caches `.venv`, runs ruff + pyright +
  pytest for each service
- Job `build`: runs `docker compose build` as a smoke-check (no push)

## Network topology

```
Client → Nginx (8080) ─┬─ /auth/*           → auth_1 (8001) │
                       │                    └ auth_2 (8001) ─┘ upstream auth (least_conn)
                       ├─ /.well-known/*    → upstream auth
                       ├─ /accounts, /transfers → core_banking (8000)
                       ├─ /history          → history (8000)
                       └─ /market/*         → bankmarket (8000)

Internal network: bank_net (bridge)
```

## Dependency graph (Compose startup order)

```
rabbitmq ←─ core_banking, history, bankmarket
auth_db  ←─ auth_1, auth_2
core_banking_db ←─ core_banking
redis    ←─ auth_1, auth_2
mongo_{1,2,3} ←─ mongo_init ←─ history
neo4j    ←─ bankmarket
auth_{1,2} ←─ nginx
core_banking ←─ nginx, bankmarket
history  ←─ nginx
bankmarket ←─ nginx
```
