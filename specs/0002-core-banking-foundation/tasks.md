# Tasks 0002: Core Banking Foundation

## Phase 1: Persistence
- [x] Task 1.1: Define SQLAlchemy tables (`accounts`, `transactions`, `outbox_events`).
- [x] Task 1.2: Initialize Alembic and generate the first migration.
- [x] Task 1.3: Implement repository methods for accounts and transfers.

## Phase 2: Domain Logic
- [x] Task 2.1: Implement `BankingService.create_account`.
- [x] Task 2.2: Implement `BankingService.transfer_money` with ACID locking and Outbox insertion.
- [x] Task 2.3: Implement the Outbox Relay background task.

## Phase 3: API Layer
- [x] Task 3.1: Implement account routes (`POST`, `GET`).
- [x] Task 3.2: Implement transfer route (`POST`).
- [x] Task 3.3: Wire everything in `api.py` and `lifespan`.

## Phase 4: Verification
- [x] Task 4.1: Write integration tests for the transfer flow.
- [x] Task 4.2: Verify outbox delivery to RabbitMQ.
