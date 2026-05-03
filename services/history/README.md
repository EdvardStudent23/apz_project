# History service

Read-side of CQRS. Consumes `TransactionCreatedEvent` from RabbitMQ,
writes to a MongoDB replica set, and exposes paginated `/history`. See
`CLAUDE.md` for the quorum / read-only behavior.

## Local run

```
uv run uvicorn src.api:app --reload --port 8004
```
