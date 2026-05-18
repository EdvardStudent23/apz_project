# Tasks: DevOps Infrastructure & API Gateway

**Plan:** [plan.md](plan.md)

---

## Task list

| # | Task | File(s) | Status |
|---|------|---------|--------|
| T1 | Create `infrastructure/Dockerfile.base` | `infrastructure/Dockerfile.base` | Done |
| T2 | Rewrite Auth service Dockerfile for uv monorepo | `services/auth/Dockerfile` | Done |
| T3 | Create Core Banking Dockerfile | `services/core_banking/Dockerfile` | Done |
| T4 | Rewrite History service Dockerfile | `services/history/Dockerfile` | Done |
| T5 | Create BankMarket Dockerfile | `services/bankmarket/Dockerfile` | Done |
| T6 | Create Nginx config | `nginx/nginx.conf` | Done |
| T7 | Create root `docker-compose.yml` | `docker-compose.yml` | Done |
| T8 | Create GitHub Actions CI workflow | `infrastructure/github-actions/ci.yml` | Done |
| T9 | Update Makefile | `Makefile` | Done |

## Verification checklist

- [ ] `make up` completes without errors from a clean state
- [ ] `curl http://localhost:8080/auth/login` reaches the auth service
- [ ] `curl http://localhost:8080/.well-known/jwks.json` returns the JWKS
- [ ] `docker compose stop auth_1` then `curl /auth/validate` still succeeds
- [ ] MongoDB replica set shows PRIMARY + 2 SECONDARY in `rs.status()`
- [ ] GitHub Actions workflow appears in the Actions tab and passes on push
