# CLAUDE.md

Guidance for Claude when working in this repository. **Read this file
in full at the start of every session.** It defines the architecture,
conventions, and the role split between the five engineers on the
team — and is the canonical context handed to a fresh Claude session.

## What this project is

A **microservices-based digital bank** with an internal product
marketplace. Five Python services collaborate over **HTTP** (sync,
request/response) and **RabbitMQ** (async, event-driven) behind a
single **Nginx** API gateway.

The system models real banking primitives: user accounts, balances,
ACID money transfers, an immutable transaction log, and a
recommendation-aware in-app store ("BankMarket").

It is built and operated as a course / portfolio project for a 2–5
person team (currently 5). Each service is owned end-to-end by one
engineer, but all services share the conventions in this document so
the system behaves as one product.

## Course requirements — compliance matrix

This project is built against a course brief. Every requirement maps
to a concrete implementation choice in this repo. **Do not break any
of these mappings without updating this table.**

| Requirement                                                      | Where it lives                                                 |
|------------------------------------------------------------------|----------------------------------------------------------------|
| Microservice architecture                                        | `services/auth`, `core_banking`, `history`, `bankmarket`       |
| Authentication microservice with login/logout                    | `services/auth` — `/register`, `/login`, `/logout`             |
| 3-tier per service: Web → Service+Domain → Repository            | `routes/` → `services/` → `db/repository.py` + `db/tables/`    |
| Separate DB per microservice                                     | Auth=Postgres, Core Banking=Postgres, History=Mongo, Market=Neo4j |
| Duplicated app server with failover + distributed session store  | Auth × 2 replicas behind Nginx, sessions in Redis              |
| Replicated NoSQL with quorum-aware failover (read-only on loss)  | MongoDB replica set (1 primary + 2 secondaries)                |
| Async processing via message queue                               | History consumes RabbitMQ; CQRS read-side                      |
| API Gateway                                                      | Nginx — single ingress on port 8080                            |
| RESTful API                                                      | All services expose REST endpoints with `ApiResponse`          |
| Password hashing                                                 | argon2id via `argon2-cffi` in Auth                             |
| Token/session destroyed on logout                                | Logout deletes `session:<jti>` from Redis                      |
| Docker / Docker Compose                                          | `docker-compose.yml` brings up the full stack                  |
| Source code repository                                           | GitHub (origin)                                                |
| Continuous integration                                           | GitHub Actions in `infrastructure/github-actions/`             |
| Task board                                                       | GitHub Projects board, linked from `README.md`                 |
| Spec-Driven Development (no raw prompts)                         | See **Spec-Driven Development** section below                  |
| Vision / use cases / backlog                                     | `docs/vision.md`, `docs/use-cases.md`, `docs/backlog.md`       |
| Architecture diagram                                             | `docs/architecture.md` + `docs/diagrams/architecture.png`      |
| Self-verified failover scenarios                                 | `docs/runbooks/failover-verification.md`                       |

## Spec-Driven Development (SDD)

The course brief explicitly forbids "AI as raw prompts" and requires
following a Spec-Driven Development framework. The artifacts that
the framework produces must be committed alongside code.

**Chosen framework: GitHub Spec Kit** (`github/spec-kit`). Picked
because it's open-source, language-agnostic, integrates cleanly with
GitHub Issues / PRs, and produces plain-Markdown artifacts that
diff well in code review. Alternatives we considered and rejected:
specs.md (lighter, less tooling), Kiro (IDE-locked), Tessl (paid).

### Workflow (required for every non-trivial change)

1. `/specify` — write a **specification** for the feature in
   `specs/<feature-id>/spec.md`. Captures user intent, acceptance
   criteria, out-of-scope items. **No implementation details.**
2. `/plan` — derive a **technical plan** in `specs/<feature-id>/plan.md`.
   Lists the affected services, schemas, events, migrations.
3. `/tasks` — break the plan into **tasks** in
   `specs/<feature-id>/tasks.md`. Each task is one PR-sized unit and
   maps to a GitHub Issue.
4. Implementation happens task by task. Each PR links back to its
   task and its spec.
5. On merge, the spec is **frozen** (git history is the audit trail).
   Changes go through a new spec rather than mutating the old one.

### Repo layout for SDD artifacts

```
specs/
├── 0001-user-registration/
│   ├── spec.md
│   ├── plan.md
│   └── tasks.md
├── 0002-money-transfer/
│   ├── spec.md
│   ├── plan.md
│   └── tasks.md
└── …
```

When Claude is asked to implement a feature, it must **read the
matching spec/plan first** and follow it. If the spec is missing or
unclear, Claude must stop and ask for it — implementing without a
spec violates the course requirement.

## Three-tier architecture (explicit)

Every service in `services/<name>/src/` is structured as three
layers, in line with the course brief:

| Layer                       | Folder            | Responsibility                                                  |
|-----------------------------|-------------------|------------------------------------------------------------------|
| Web / API layer             | `routes/`         | FastAPI routers, request/response schemas, HTTP concerns only    |
| Service + Domain layer      | `services/`       | Business logic, domain rules, orchestration across repositories  |
| Repository / Persistence    | `db/repository.py` + `db/tables/` (or `messaging/`, Mongo collections, Cypher queries) | Data access only — no business rules |

**Routes never touch the DB directly. Repositories never raise HTTP
errors.** Crossing these boundaries is a code-review-blocking issue.

## Tech stack (frozen — do not deviate without team agreement)

- **Python ≥ 3.13**, package manager **uv**
- **FastAPI** + **uvicorn** for every service (yes, even Core Banking
  — we picked one language so people can review each other's code)
- **structlog** for structured JSON logging
- **pydantic-settings** for env-driven config
- **async SQLAlchemy 2.0** + **asyncpg** for Postgres
- **Alembic** for SQL migrations (per service)
- **redis-py** (async) for sessions, caches, rate limits
- **aio-pika** for RabbitMQ producers/consumers
- **motor** (async MongoDB driver) for the History Service
- **neo4j** official driver (async) for BankMarket recommendations
- **PyJWT** for token signing/verification
- **Nginx** as the single ingress; Docker Compose orchestrates everything
- **pyright** + **ruff** for typing/lint; CI gates on both

If a feature seems to need a new dependency, raise it in chat before
adding it to a `pyproject.toml`.

## Repository layout

This is a **monorepo**. Each service is a self-contained Python
package; shared code lives in `libs/`.

```
bank-microservices/
├── docker-compose.yml         # owned by Person #1 — brings the whole stack up
├── nginx/
│   └── nginx.conf             # gateway routing + Auth upstream load-balancing
├── infrastructure/
│   ├── Dockerfile.base        # shared Python base image
│   └── github-actions/        # CI workflows
├── libs/
│   ├── common/                # shared pydantic schemas (ApiResponse, ErrorBody)
│   ├── logging/               # structlog config + middleware
│   ├── messaging/             # aio-pika helpers, event envelopes, retry policy
│   └── auth_client/           # JWT verification helper used by all services
├── services/
│   ├── auth/                  # Person #2 — FastAPI + Postgres + Redis sessions
│   ├── core_banking/          # Person #3 — FastAPI + Postgres + RabbitMQ producer
│   ├── history/               # Person #4 — FastAPI + MongoDB + RabbitMQ consumer
│   ├── bankmarket/            # Person #5 — FastAPI + Neo4j + RabbitMQ producer
│   └── _template/             # starter skeleton — copy this when adding a service
├── specs/                     # Spec-Driven Development artifacts (spec → plan → tasks)
└── docs/
    ├── vision.md              # short product vision (course deliverable)
    ├── use-cases.md           # use cases + product backlog (course deliverable)
    ├── backlog.md             # prioritized backlog, linked to GitHub Issues
    ├── architecture.md        # system architecture narrative
    ├── diagrams/
    │   ├── architecture.png   # C4 / component diagram (course deliverable)
    │   └── sequence-transfer.png
    ├── events.md              # canonical event schemas (TransactionCreatedEvent, …)
    └── runbooks/
        ├── failover-verification.md   # how to prove Auth replica failover works
        └── mongo-quorum.md             # how to prove Mongo goes read-only on quorum loss
```

### Inside each service (consistent pattern)

```
services/<name>/
├── pyproject.toml
├── alembic.ini                # only if service uses Postgres
├── migrations/                # only if service uses Postgres
├── src/
│   ├── __init__.py
│   ├── api.py                 # FastAPI app + lifespan
│   ├── settings.py            # pydantic-settings, env-driven
│   ├── middleware.py          # RequestId, Exception (mirror instagram-android)
│   ├── routes/
│   │   ├── <feature>/routes.py
│   │   ├── <feature>/schemas.py
│   │   └── common/            # auth dependency, ApiResponse, error mapping
│   ├── services/              # business logic
│   ├── db/
│   │   ├── core.py            # engine + session factory + Base
│   │   ├── repository.py      # data-access functions
│   │   └── tables/            # SQLAlchemy models
│   ├── messaging/             # RabbitMQ producer/consumer wiring
│   └── clients/               # outbound HTTP clients to other services
└── tests/
```

`services/_template/` is a working skeleton: when you add a sixth
service later, copy this folder and rename — do not invent a new
layout.

## Team split (single source of truth)

| # | Person  | Service / area     | Owns                                                                                     |
|---|---------|--------------------|------------------------------------------------------------------------------------------|
| 1 | DevOps  | Gateway & infra    | Nginx, docker-compose, GitHub Actions CI, RabbitMQ + Mongo replica set provisioning      |
| 2 | Auth    | `services/auth`    | `/register`, `/login`, `/logout`, JWT issuing, Redis-backed sessions, users in Postgres  |
| 3 | Banking | `services/core_banking` | Accounts, balances, ACID transfers, publishes `TransactionCreatedEvent`             |
| 4 | History | `services/history` | RabbitMQ consumer → MongoDB replica set, `/history` read API                             |
| 5 | Market  | `services/bankmarket` | Catalog, purchase flow, Neo4j-backed recommendations, calls Core Banking over HTTP    |

When implementing a feature, **only touch the service you own**, except:
- shared schemas → `libs/common`,
- new event types → `libs/messaging` + `docs/events.md` (must be PR-reviewed by both producer and consumer owners),
- shared infra → `docker-compose.yml`, `nginx/`.

## Inter-service contract (HTTP + events)

### HTTP between services

- Always go through Nginx **except** for service-to-service traffic
  inside the docker network — there, address services by container
  name (`http://core_banking:8000`).
- Every request must carry `Authorization: Bearer <jwt>`. Services
  verify JWTs locally using `libs/auth_client` (no per-request hop to
  Auth Service — too slow). Auth's public key is fetched once at
  startup in `lifespan`.
- Propagate `x-request-id` across hops. The middleware in
  `libs/logging` reads or generates it; outbound HTTP clients must
  forward it. This makes a single banking transaction traceable
  across all five services.
- Every endpoint returns the shared `ApiResponse` envelope:
  ```python
  class ApiResponse(BaseModel):
      status: bool
      response: Any  # str on failure, payload on success
  ```
  Errors map to HTTP status via the exception middleware — never
  manually `JSONResponse(status_code=...)`.

### Events over RabbitMQ

- One **topic exchange** per producer service: `core_banking.events`,
  `bankmarket.events`. Consumers bind their own queue with a routing
  key pattern.
- All event payloads inherit from `libs/messaging.EventEnvelope`:
  ```python
  class EventEnvelope(BaseModel):
      event_id: str          # uuid4
      event_type: str        # e.g. "transaction.created"
      occurred_at: datetime  # UTC, ISO-8601
      producer: str          # service name
      request_id: str | None # for tracing
      payload: dict          # type-specific, validated by consumer
  ```
- Consumers must be **idempotent** keyed on `event_id`. The History
  Service stores `event_id` with a unique index in Mongo.
- Schema changes to events are **breaking** unless additive. New
  fields → optional with defaults. Renames/removals → introduce a new
  `event_type`, dual-publish, then retire.
- Canonical schemas live in `docs/events.md`. Keep it in sync.

## Critical flow: money transfer

This is the most important flow to keep correct end-to-end.

1. Client → Nginx → `POST /transfers` on Core Banking (JWT-authed).
2. Core Banking opens a Postgres transaction:
   - locks both account rows (`SELECT … FOR UPDATE`) in deterministic
     order (smaller `account_id` first) to avoid deadlocks,
   - validates funds + currency,
   - writes a `transactions` row,
   - debits source, credits destination,
   - commits.
3. **After commit**, publishes `TransactionCreatedEvent` to
   `core_banking.events` with routing key `transaction.created`.
   Use the **transactional outbox pattern**: the event row is written
   inside the same Postgres transaction in step 2, and a relay
   coroutine drains the outbox to RabbitMQ. This is the only way to
   guarantee "money moved ⇒ event published" without a 2PC.
4. History Service consumer picks up the event, writes to MongoDB
   (replica set, write concern `majority`).
5. BankMarket purchase flows hit the same `/transfers` endpoint with
   a `purpose: marketplace_purchase` field, then publish their own
   `bankmarket.purchase` event to seed the Neo4j recommendation graph.

**Do not skip the outbox.** Publishing to RabbitMQ from inside the
DB transaction is not durable; publishing after commit can lose
events on crash. The outbox is the standard fix and is non-negotiable.

## Auth Service specifics

- Sessions live in **Redis**, keyed by `session:<jti>`, value is a
  JSON blob with `user_id`, `issued_at`, `device`. JWT carries `jti`;
  logout deletes the Redis key, revoking the token immediately.
- Two replicas of Auth run behind Nginx (`upstream auth { … }`,
  `least_conn`). Sessions in Redis are the reason a fail-over of one
  replica leaves the user logged in — that requirement is the whole
  point of Redis here.
- User passwords: argon2id (`argon2-cffi`). Never bcrypt, never
  plaintext, never reversible.
- Public key for JWT verification is exposed at `GET /.well-known/jwks.json`.
  Other services fetch it once in `lifespan`.

## History Service specifics

- MongoDB **replica set** (1 primary + 2 secondaries) — provisioned
  in `docker-compose.yml`. Reads use `readPreference=secondaryPreferred`,
  writes use `w=majority`.
- **Quorum behavior** (course requirement): when fewer than 2 of 3
  nodes are reachable, the replica set loses majority and Mongo
  automatically demotes to **read-only** — no primary can be elected,
  writes fail. Verified in `docs/runbooks/mongo-quorum.md`.
- Consumer ack policy: ack only after a successful Mongo write. Use
  a DLQ (`history.dlq`) for poison messages.
- `GET /history?user_id=...` is paginated (cursor-based, not offset).
  Indexes: `(user_id, occurred_at desc)`, `event_id unique`.
- This service is the **read side of CQRS**: it never owns the truth
  for transactions (Core Banking does). It builds a denormalized
  read model from events. Treat it as eventually consistent.

## BankMarket specifics

- Neo4j stores `(:User)-[:BOUGHT {at}]->(:Product)` and
  `(:Product)-[:CATEGORY]->(:Category)`. Recommendations use a
  collaborative-filtering Cypher query — see `services/bankmarket/src/services/recommend.py`.
- Purchases call Core Banking's `/transfers` synchronously (HTTP). If
  the transfer fails, the purchase fails — no half-states.
- After a successful transfer, BankMarket publishes
  `bankmarket.purchase` to its own exchange. Itself consumes that
  event to update Neo4j (single writer pattern keeps the graph
  consistent even on retries).

## Conventions every service follows

### FastAPI app shape

Mirror `instagram-android`'s `src/api.py`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging("<service-name>")
    # init: redis, db engine + session factory, rabbitmq, http clients
    yield
    # teardown in reverse order

app = FastAPI(title="<service>", lifespan=lifespan)
app.add_middleware(ExceptionMiddleware)
app.add_middleware(RequestIdMiddleware)
app.include_router(...)
```

### Settings

`pydantic-settings` with `env_file=".env"`, `extra="ignore"`. **Nothing
hardcoded.** Every external URL, secret, feature flag is an env var.
Imported as `from src.settings import settings`.

### Logging

```python
import structlog
logger = structlog.get_logger(__name__)

logger.info("transfer completed", from_account=..., to_account=..., amount=...)
```

- Structured kwargs only — never f-strings inside log messages.
- Bind per-request context via `bind_contextvars(...)` at the route
  entry; downstream logs inherit it automatically.
- JSON to stdout. Filebeat ships logs in deployed environments.

### Database (Postgres services)

- One Postgres database per service — **no shared schema**. The Auth
  DB and Core Banking DB never see each other's tables.
- Async SQLAlchemy. Get the session from
  `request.app.state.db_sessionmaker`.
- Migrations live in `services/<name>/migrations/`. Each service has
  its own Alembic chain.
- Repository pattern: data-access functions go in
  `src/db/repository.py`, not in routes. Routes call repositories;
  repositories call the session.

### Errors

- Domain errors → specific exceptions in `src/services/exceptions.py`
  (`InsufficientFunds`, `AccountNotFound`, …).
- Map them to HTTP status in the exception middleware in one place.
- Never raise `Exception("...")` — always something specific.

### Testing

- `pytest` + `pytest-asyncio` + `httpx.AsyncClient` for HTTP.
- Integration tests run against real Postgres / Redis / RabbitMQ /
  Mongo / Neo4j containers (Compose profile `test`). **No mocks for
  the database** — we want to catch migration drift.
- One e2e test per critical flow: `register → login → transfer → history → recommendation`.

### Code style

- `from __future__ import annotations` in every new file.
- Type-hint everything; `pyright` is strict, CI fails on errors.
- `pathlib.Path` over `os.path`.
- Default to no comments — name things well. Comment only when *why*
  is non-obvious.
- No emojis in code, commits, or PRs.

## Common commands

Run from repo root unless noted.

```
make up                         # docker compose up -d
make down                       # docker compose down
make logs SVC=auth              # tail one service
make ruff                       # format every service
make lint                       # pyright + ruff across all services

# Per-service:
cd services/<name> && uv run uvicorn src.api:app --reload --port <port>
cd services/<name> && uv run alembic upgrade head
cd services/<name> && uv run alembic revision --autogenerate -m "..."

# E2E:
make test-e2e                   # spins compose profile=test, runs pytest
```

Service ports (development):
- Nginx gateway: `8080`
- Auth: `8001` / `8002` (two replicas)
- Core Banking: `8003`
- History: `8004`
- BankMarket: `8005`

## When making changes

- **Touching event schemas** → update `docs/events.md`, bump consumer
  parsers, coordinate with the consumer service owner *before* merging.
- **Adding a new endpoint** → add route + schemas + repository func +
  test, in that order. Update Nginx routing only if it should be
  public.
- **New persistent field on a model** → add to the SQLAlchemy table,
  generate an Alembic revision, run `make db-upgrade` locally, commit
  the migration.
- **New cross-service call** → use `libs/auth_client` to forward JWT;
  use the shared HTTP client factory; propagate `x-request-id`.
- **Touching the transfer flow in Core Banking** → re-run the e2e
  test before opening a PR. Money correctness > velocity.

## Failover verification (course requirement)

The brief says "обовʼязково перевірте самостійно, що такий сценарій у
вас працює" — we must **prove** the failover scenarios work, not just
configure them. The exact procedures live in
`docs/runbooks/failover-verification.md`; the summary:

### Auth replica failover (session continuity)

1. `make up`, register a user, log in, capture the JWT.
2. Hit a JWT-protected endpoint via Nginx — succeeds.
3. `docker compose stop auth_1` (kill one replica).
4. Hit the same endpoint again — must still succeed (Nginx routes to
   `auth_2`, session is in Redis, not in-process).
5. `docker compose start auth_1`. Logout. Token must be invalidated
   on **both** replicas immediately.

### Mongo quorum read-only

1. `make up`, send a few transfers so History has data.
2. `docker compose stop mongo_2 mongo_3` (kill two of three nodes).
3. New transfer → consumer write must **fail with no primary** (or
   the queue should back up); `GET /history` reads from the surviving
   secondary still succeed (`readPreference=secondaryPreferred`).
4. Bring nodes back, verify the consumer drains the backlog from
   RabbitMQ — no events lost.

Both procedures must be re-run before any release tag and the result
recorded in the runbook with a date.

## Anti-patterns (do not do these)

- Sharing a database between services. Each service owns its data;
  cross-service reads go through HTTP or events.
- Publishing events without the outbox pattern in transactional flows.
- Using mocks where a real container would do — see Testing.
- Catching `Exception` and swallowing it. Let the middleware log it.
- Adding a "quick endpoint" to a service you don't own.
- Bypassing the gateway in production traffic.
- Adding a new dependency without raising it in chat first.
- Implementing a feature without a `specs/<feature-id>/` artifact —
  violates the course's Spec-Driven Development requirement.
- Putting business logic in `routes/` or HTTP concerns in
  `db/repository.py` — breaks the 3-tier layering the brief requires.

## Cross-session context for Claude

This file is the spine. When a fresh Claude session starts:

1. Read this file in full.
2. Read `docs/vision.md`, `docs/use-cases.md`, `docs/architecture.md`,
   and `docs/events.md`.
3. If the task references a feature, read its
   `specs/<feature-id>/{spec,plan,tasks}.md` before writing any code.
   No spec → stop and ask.
4. If working inside one service, read that service's
   `services/<name>/README.md` (each owner maintains a short one).
5. Only then start the task.

Persistent decisions, post-mortems, and design rationale go in
`docs/`, not in commit messages — commits get lost in `git log`,
docs don't.
