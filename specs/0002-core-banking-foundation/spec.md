# Spec 0002: Core Banking Foundation

## Status
- **Status:** Proposed
- **Owner:** Person #3 (Core Banking)
- **Stakeholders:** Person #4 (History), Person #5 (BankMarket)

## User Intent
As a NanoBank user, I want to manage my money through multiple accounts and securely transfer funds to other users. As a developer, I want a reliable way to ensure that every successful transfer triggers an event for downstream services without data loss.

## Acceptance Criteria
- **Account Management:**
  - Users can create accounts in different currencies (e.g., USD, EUR, UAH).
  - Users can view a list of their accounts and current balances.
- **Money Transfers:**
  - Users can transfer money from one of their accounts to another account (local or other user's).
  - Transfers must be ACID-compliant: money must never "disappear" or be "created" during a transfer.
  - Insufficient funds or invalid currencies must prevent the transfer.
- **Event Reliability:**
  - Every successful transfer must eventually result in a `TransactionCreatedEvent` published to RabbitMQ.
  - The system must handle RabbitMQ unavailability without losing events (Transactional Outbox).

- **Currency Conversion:**
  - The service supports transfers between different currencies using internal fixed exchange rates (for this phase).
  - The conversion happens automatically during the transfer process.

## Out of Scope
- External bank transfers (SWIFT/SEPA).
- Real-time exchange rate API integration (uses internal rates).
- Detailed transaction history (handled by History Service).

## User Stories
1. **Create Account:** "I want to open a new USD account so I can start saving."
2. **Check Balance:** "I want to see how much money I have in my EUR account."
3. **Transfer Money:** "I want to send 100 USD to my friend's account securely."
