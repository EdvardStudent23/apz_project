# BankMarket service

In-app product marketplace with Neo4j-backed recommendations. Calls
Core Banking's `/transfers` synchronously to settle purchases. See
`CLAUDE.md` for the purchase flow.

## Local run

```
uv run uvicorn src.api:app --reload --port 8005
```
