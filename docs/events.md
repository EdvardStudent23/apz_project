# Events

Canonical event schemas published over RabbitMQ. All events extend
`messaging.EventEnvelope` (`libs/messaging/src/messaging/envelope.py`).

## `transaction.created`

Published by `core_banking` service after a successful money transfer.

**Routing Key:** `transaction.created`
**Exchange:** `core_banking.events`

**Payload:**
```json
{
  "transaction_id": "uuid",
  "sender_account_id": "uuid",
  "receiver_account_id": "uuid",
  "amount": "decimal",
  "currency": "string (3 chars)",
  "purpose": "string",
  "occurred_at": "iso8601"
}
```
