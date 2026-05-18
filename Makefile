.PHONY: up down logs build ruff lint test test-e2e db-upgrade

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
# Runs Alembic upgrade head for every Postgres-backed service.
db-upgrade:
	cd services/auth        && uv run alembic upgrade head
	cd services/core_banking && uv run alembic upgrade head
