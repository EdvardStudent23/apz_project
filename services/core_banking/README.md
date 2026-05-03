# Core Banking Service

Responsible for managing accounts, balances, and ACID-compliant money transfers. It acts as the "source of truth" for all financial state in NanoBank.

## Features
- **Account Management:** Create and list accounts in various currencies.
- **ACID Transfers:** Atomic money transfers with deadlock prevention.
- **Transactional Outbox:** Guaranteed event delivery to RabbitMQ via the outbox pattern.
- **JWT Authentication:** Locally verified tokens via JWKS from the Auth Service.

## Architecture
Follows the 3-tier pattern:
1. **Web Layer (`src/routes/`):** FastAPI routers and Pydantic schemas.
2. **Service Layer (`src/services/`):** Business logic, transaction management, and locking.
3. **Persistence Layer (`src/db/`):** SQLAlchemy models and repository pattern.

## API Endpoints

### Accounts
- `POST /accounts`: Open a new account.
  - Body: `{"currency": "USD"}`
- `GET /accounts`: List all accounts for the current user.

### Transfers
- `POST /transfers`: Transfer money between accounts.
  - Body: `{"sender_account_id": "...", "receiver_account_id": "...", "amount": 100.0, "purpose": "Dinner"}`
  - Note: Both accounts must have the same currency.

## Technical Details

### Deadlock Prevention
When locking accounts for a transfer, the service sorts account IDs and locks the one with the smaller UUID first. This ensures a consistent locking order across all concurrent requests, preventing circular wait conditions.

### Transactional Outbox
Every successful transfer writes a `TransactionCreatedEvent` to the `outbox_events` table in the same database transaction. A background relay task (`OutboxRelay`) polls this table and publishes events to RabbitMQ. This ensures that money never moves without an event being sent, even if RabbitMQ is temporarily unavailable.

## Development & Testing

### Running the Demo
For local testing when the Auth Service is not running, the Core Banking Service will automatically enable an **authentication bypass mode**.

1.  Start dependencies:
    ```bash
    docker compose -f docker-compose.deps.yml up -d
    ```
2.  Apply migrations:
    ```bash
    uv run alembic upgrade head
    ```
3.  Run the service:
    ```bash
    uv run uvicorn src.api:app --reload --port 8003
    ```
4.  Run the demo script:
    ```bash
    uv run client_demo.py
    ```

### Running Tests
```bash
# Run all tests with coverage
uv run pytest --cov=src tests/
```
