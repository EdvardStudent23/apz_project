# Auth service

Owns user registration, login/logout, JWT issuance, and Redis-backed
sessions. See `CLAUDE.md` for the full contract.

## Local run

```
uv run uvicorn src.api:app --reload --port 8001
```
