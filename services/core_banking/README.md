# Core Banking service

Owns accounts, balances, ACID money transfers, and the
`TransactionCreatedEvent` producer (transactional outbox). See
`CLAUDE.md` for the transfer flow.

## Local run

```
uv run uvicorn src.api:app --reload --port 8003
```
