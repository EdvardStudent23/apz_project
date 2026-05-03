# Service template

Starter skeleton for a new service. Copy this directory, rename to your
service, and start filling in routes, services, and repositories.

If your service does not use Postgres, delete `alembic.ini` and
`migrations/`, and replace `src/db/core.py` with the appropriate driver
(see `services/history` for Mongo, `services/bankmarket` for Neo4j).

## Local run

```
uv run uvicorn src.api:app --reload --port 8000
```
