.PHONY: ruff lint test up down logs test-e2e db-upgrade

ruff:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff check .
	uv run pyright

test:
	uv run pytest

up:
	@echo "TODO (Person #1): docker-compose.yml not in scaffold yet"

down:
	@echo "TODO (Person #1): docker-compose.yml not in scaffold yet"

logs:
	@echo "TODO (Person #1): docker-compose.yml not in scaffold yet (usage: make logs SVC=auth)"

test-e2e:
	@echo "TODO (Person #1): docker compose profile=test not in scaffold yet"

db-upgrade:
	@echo "TODO (Person #1): wire per-service alembic upgrade head"
