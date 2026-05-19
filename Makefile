.PHONY: up down logs build ruff lint test test-e2e test-failover \
	db-update db-upgrade db-revision web-dev web-build

# ── Stack lifecycle ────────────────────────────────────────────────────────────
up:
	docker-compose up -d --build

down:
	docker-compose down

# Usage: make logs SVC=auth_1
logs:
	docker-compose logs -f $(SVC)

build:
	docker-compose build

# ── Code quality ───────────────────────────────────────────────────────────────
ruff:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff check .
	uv run pyright

# ── Tests ──────────────────────────────────────────────────────────────────────
test:
	uv run pytest

# Run e2e tests against the running stack (excludes slow failover tests).
# Usage: make up && make test-e2e
test-e2e:
	uv run pytest tests/e2e/ -v -m "not failover"

# Run failover/quorum tests — these stop/start containers; run after make up.
test-failover:
	uv run pytest tests/e2e/ -v -m failover --timeout=120

# ── Database migrations ────────────────────────────────────────────────────────
# List of Postgres-backed services with their own Alembic migration chain.
# Add new services here when they start using Postgres.
PG_SERVICES := auth core_banking

# Apply pending migrations across every Postgres-backed service.
# Usage: make db-update            # apply all
#        make db-update SVC=auth   # apply for a single service
db-update:
ifdef SVC
	cd services/$(SVC) && uv run alembic upgrade head
else
	@for svc in $(PG_SERVICES); do \
		echo "==> $$svc: alembic upgrade head"; \
		(cd services/$$svc && uv run alembic upgrade head) || exit $$?; \
	done
endif

# Generate a new Alembic revision for one service.
# Usage: make db-revision SVC=auth MSG="add users.email_verified"
db-revision:
ifndef SVC
	$(error SVC is required, e.g. make db-revision SVC=auth MSG="add ...")
endif
ifndef MSG
	$(error MSG is required, e.g. make db-revision SVC=auth MSG="add ...")
endif
	cd services/$(SVC) && uv run alembic revision --autogenerate -m "$(MSG)"

# Back-compat alias — older docs / CLAUDE.md reference `make db-upgrade`.
db-upgrade: db-update

# ── Web UI ─────────────────────────────────────────────────────────────────────
web-dev:
	cd web && npm install && npm run dev

web-build:
	cd web && npm install && npm run build
