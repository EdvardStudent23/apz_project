# Initial Repository Scaffold — Design

## Goal

Lay down the directory tree and compilable Python stubs for the
microservices-based digital bank described in `CLAUDE.md`, so each
team member has a working starting point in their service. No Docker,
no Nginx, no databases yet — those belong to the DevOps owner and will
land in a later spec.

CLAUDE.md is the authoritative spec for layout, tech stack, and
conventions. This document captures only the choices we made *about
how to scaffold*, not the architecture itself.

## Scope

**In scope (Option B, "compilable stubs"):**

- Top-level repo files: `.gitignore`, `Makefile` (with the targets
  named in CLAUDE.md; Docker-dependent targets stubbed with `@echo
  "TODO: Person #1"`).
- `libs/` — four packages (`common`, `logging`, `messaging`,
  `auth_client`), each a uv workspace member with its own
  `pyproject.toml`. Real implementations for the small,
  service-agnostic pieces:
  - `common.schemas.ApiResponse`, `ErrorBody`
  - `logging.config` (structlog setup), `logging.middleware`
    (RequestId binding)
  - `messaging.envelope.EventEnvelope`
  - `auth_client.jwt.verify_jwt` (PyJWT-based)
- `services/_template/` — full skeleton matching the per-service
  layout in CLAUDE.md.
- `services/{auth, core_banking, history, bankmarket}/` — copies of
  `_template` with service-appropriate variations:
  - Postgres services (`auth`, `core_banking`) get `alembic.ini` +
    empty `migrations/` chain and `db/core.py` wired for async
    SQLAlchemy.
  - `history` gets a Motor (async MongoDB) client stub in `db/core.py`
    instead of SQLAlchemy.
  - `bankmarket` gets an async Neo4j driver stub in `db/core.py`.
- `docs/` — placeholder files (H1 only) for `vision.md`,
  `use-cases.md`, `backlog.md`, `architecture.md`, `events.md`,
  `runbooks/failover-verification.md`, `runbooks/mongo-quorum.md`.
  `diagrams/` with `.gitkeep`.
- `specs/` — `.gitkeep` only. Real specs come per feature under SDD.
- `infrastructure/github-actions/` — `.gitkeep`.

**Out of scope (deferred to later specs / Person #1):**

- `docker-compose.yml`
- `nginx/nginx.conf`
- `infrastructure/Dockerfile.base`
- GitHub Actions workflows
- Any actual DB schema, migration content, or business logic
- Concrete event types beyond the envelope
- Tests beyond empty `tests/__init__.py` per service

## Key decisions

### 1. Python version

Every `pyproject.toml` pins `requires-python = ">=3.13"`, matching
CLAUDE.md.

### 2. uv workspace, deps split per service

A single root `pyproject.toml` declares the workspace; each service
and each lib is a workspace member with its own `pyproject.toml` and
its own dependencies. No deps are pooled.

**Why workspace over path-deps:**

- One `uv sync` from root brings up the whole repo.
- Changes in `libs/*` are picked up by services without re-syncing.
- Single lockfile, single `.venv`, simpler IDE / pyright setup.
- Each service still owns its own dependency list — Auth pins
  `argon2-cffi`, History pins `motor`, BankMarket pins `neo4j`, etc.

The only downside (extracting a service into its own repo later) is
not a real concern for this project.

### 3. Real vs. stub code in the scaffold

- **Real (small, service-agnostic, mandated by CLAUDE.md):**
  `ApiResponse`, `ErrorBody`, `EventEnvelope`, structlog config,
  RequestId middleware, `verify_jwt`, FastAPI app + lifespan in
  `api.py`, pydantic-settings `Settings` class.
- **Stub (real type signatures, `raise NotImplementedError` or
  `pass`):** repository functions, messaging producers/consumers,
  outbound HTTP clients, JWKS fetching.

Routes are intentionally left empty — the scaffold should expose **no
HTTP endpoints yet**. Routes belong to per-feature specs under SDD.

### 4. Conventions enforced by the scaffold

- `from __future__ import annotations` at the top of every `.py`
  file.
- No emojis, no comments unless *why* is non-obvious.
- `pyright` clean against the scaffold (CI doesn't exist yet, but the
  scaffold should not generate type errors when CI lands).
- No hardcoded URLs or secrets — every external dependency comes
  through `Settings`.

## Acceptance criteria

1. From a fresh checkout: `uv sync` at the repo root succeeds.
2. `uv run pyright` reports zero errors.
3. `uv run ruff check` reports zero errors.
4. For each service: `cd services/<name> && uv run python -c "from
   src.api import app"` succeeds (FastAPI app importable, no routes
   registered).
5. Directory tree matches the "Repository layout" and "Inside each
   service" sections of `CLAUDE.md` exactly.
6. No `docker-compose.yml`, `nginx/`, or `Dockerfile.base` exists.
   The Makefile targets that would need them print a TODO.

## Open risks

- **CLAUDE.md drift.** If a layout decision in this scaffold conflicts
  with CLAUDE.md, CLAUDE.md wins; update the scaffold rather than
  silently diverging.
- **uv workspace + path resolution.** pyright sometimes needs a
  `pyrightconfig.json` with `extraPaths` for workspace members. We'll
  add one if `uv run pyright` complains.
