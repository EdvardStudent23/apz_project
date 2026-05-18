from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from src.db.repository import BankingRepository
from src.db.tables import Account, Transaction
from src.services.exceptions import (
    AccountNotFound,
    CurrencyMismatch,
    InsufficientFunds,
    InvalidAmount,
    UnauthorizedAccount,
)


class BankingService:
    def __init__(self, repository: BankingRepository) -> None:
        self.repository = repository

    async def create_account(self, user_id: UUID, currency: str, initial_balance: float = 0.0) -> Account:
        return await self.repository.create_account(user_id, currency.upper(), initial_balance)

    async def get_user_accounts(self, user_id: UUID) -> list[Account]:
        return await self.repository.get_accounts_by_user(user_id)

    async def transfer_money(
        self,
        user_id: UUID,
        sender_account_id: UUID,
        receiver_account_id: UUID,
        amount: float,
        purpose: str | None = None,
        request_id: str | None = None,
    ) -> Transaction:
        decimal_amount = Decimal(str(amount))
        if decimal_amount <= 0:
            raise InvalidAmount("Amount must be positive")

        # Order account IDs to prevent deadlocks (smaller UUID first)
        ordered_ids = sorted([sender_account_id, receiver_account_id])

        # Lock accounts in order
        accounts_map: dict[UUID, Account] = {}
        for account_id in ordered_ids:
            account = await self.repository.get_account_for_update(account_id)
            if not account:
                raise AccountNotFound(f"Account {account_id} not found")
            accounts_map[account_id] = account

        sender = accounts_map[sender_account_id]
        receiver = accounts_map[receiver_account_id]

        # Verify sender account belongs to the authenticated user
        if sender.user_id != user_id:
            raise UnauthorizedAccount("Sender account does not belong to this user")

        # Calculate target amount with conversion if needed
        target_amount = decimal_amount
        if sender.currency != receiver.currency:
            # Basic internal conversion rates (base USD)
            rates = {
                "USD": Decimal("1.0"),
                "EUR": Decimal("0.92"),
                "UAH": Decimal("39.5")
            }
            if sender.currency in rates and receiver.currency in rates:
                usd_amount = decimal_amount / rates[sender.currency]
                target_amount = usd_amount * rates[receiver.currency]
            else:
                raise CurrencyMismatch(
                    f"Unsupported currency for conversion: {sender.currency} or {receiver.currency}"
                )

        if sender.balance < decimal_amount:
            raise InsufficientFunds(
                f"Required {decimal_amount}, available {sender.balance}"
            )

        # Execute transfer
        sender.balance -= decimal_amount
        receiver.balance += target_amount

        # Record transaction
        transaction = await self.repository.create_transaction(
            sender_id=sender_account_id,
            receiver_id=receiver_account_id,
            amount=decimal_amount,
            currency=sender.currency,
            purpose=purpose,
            request_id=request_id,
        )

        # Transactional Outbox
        await self.repository.create_outbox_event(
            event_type="transaction.created",
            payload={
                "transaction_id": str(transaction.id),
                "sender_account_id": str(sender_account_id),
                "receiver_account_id": str(receiver_account_id),
                "sender_user_id": str(sender.user_id),
                "receiver_user_id": str(receiver.user_id),
                "amount": float(decimal_amount),
                "target_amount": float(target_amount),
                "sender_currency": sender.currency,
                "receiver_currency": receiver.currency,
                "purpose": purpose,
                "occurred_at": transaction.created_at.isoformat(),
            },
        )

        return transaction
