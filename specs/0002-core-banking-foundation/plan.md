# Technical Plan 0002: Core Banking Foundation

## Architecture Overview
The Core Banking Service uses a 3-tier architecture (Routes → Services → Repositories) with a PostgreSQL database. It ensures atomicity of money transfers using database transactions and reliability of event delivery via the Transactional Outbox pattern.

## Data Models (PostgreSQL)

### `accounts`
- `id`: UUID (Primary Key)
- `user_id`: UUID (Indexed)
- `currency`: String (3 chars, e.g., "USD")
- `balance`: Numeric(20, 2) (Must be >= 0)
- `created_at`: Timestamp

### `transactions`
- `id`: UUID (Primary Key)
- `sender_account_id`: UUID (Foreign Key)
- `receiver_account_id`: UUID (Foreign Key)
- `amount`: Numeric(20, 2)
- `currency`: String
- `purpose`: String
- `request_id`: String (Tracing)
- `created_at`: Timestamp

### `outbox_events`
- `id`: UUID (Primary Key)
- `event_type`: String (e.g., "transaction.created")
- `payload`: JSONB
- `processed`: Boolean (Default: False)
- `created_at`: Timestamp

## Critical Flow: Money Transfer (ACID)
1. Start DB Transaction.
2. Lock account rows: `SELECT * FROM accounts WHERE id IN (sender_id, receiver_id) FOR UPDATE`.
   - **Crucial:** Sort IDs and lock the smaller ID first to prevent deadlocks.
3. Validate:
   - Both accounts exist.
   - Sender has sufficient funds.
4. Execute:
   - If currencies differ, apply exchange rate: `target_amount = amount * rate`.
   - Debit sender: `UPDATE accounts SET balance = balance - amount WHERE id = sender_id`.
   - Credit receiver: `UPDATE accounts SET balance = balance + target_amount WHERE id = receiver_id`.
   - Insert `transactions` record (with original amount and target amount).
   - Insert `outbox_events` record.
5. Commit Transaction.

## Transactional Outbox Relay
A background coroutine will:
1. Fetch `processed=False` events from `outbox_events`.
2. For each event:
   - Publish to RabbitMQ exchange `core_banking.events` with routing key `transaction.created`.
   - On success: `UPDATE outbox_events SET processed = True WHERE id = event_id` (or delete row).

## Endpoints
- `POST /accounts`: Create a new account for the authenticated user.
- `GET /accounts`: List accounts for the authenticated user.
- `POST /transfers`: Initiate a money transfer.

## Events
- **Exchange:** `core_banking.events` (Topic)
- **Routing Key:** `transaction.created`
- **Payload:**
  ```json
  {
    "transaction_id": "...",
    "sender_account_id": "...",
    "receiver_account_id": "...",
    "amount": 100.0,
    "currency": "USD",
    "occurred_at": "..."
  }
  ```
