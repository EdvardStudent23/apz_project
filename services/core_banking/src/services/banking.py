from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from datetime import datetime, timezone

from src.db.repository import BankingRepository
from src.db.tables import Account, Hold, Transaction
from src.services.exceptions import (
    AccountClosed,
    AccountNotEmpty,
    AccountNotFound,
    CurrencyMismatch,
    HoldAlreadyResolved,
    HoldNotFound,
    InsufficientFunds,
    InvalidAmount,
    UnauthorizedAccount,
)


# Internal FX rates relative to USD. Shared with the transfer flow so a hold's
# converted amount matches what a same-direction transfer would move.
FX_RATES: dict[str, Decimal] = {
    "USD": Decimal("1.0"),
    "EUR": Decimal("0.92"),
    "UAH": Decimal("44.5"),
}


def convert_amount(amount: Decimal, src: str, dst: str) -> Decimal:
    if src == dst:
        return amount
    if src not in FX_RATES or dst not in FX_RATES:
        raise CurrencyMismatch(f"Unsupported currency for conversion: {src} or {dst}")
    usd = amount / FX_RATES[src]
    return (usd * FX_RATES[dst]).quantize(Decimal("0.01"))


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

        if sender.is_closed:
            raise AccountClosed("Sender account is closed")
        if receiver.is_closed:
            raise AccountClosed("Recipient account is closed")

        # Calculate target amount with conversion if needed
        target_amount = convert_amount(decimal_amount, sender.currency, receiver.currency)

        # The user can only spend funds that aren't already on hold.
        if sender.available_balance < decimal_amount:
            raise InsufficientFunds(
                f"Required {decimal_amount}, available {sender.available_balance} "
                f"(of which {sender.held_balance} is on hold)"
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

    # ── Holds ────────────────────────────────────────────────────────────

    async def place_hold(
        self,
        user_id: UUID,
        account_id: UUID,
        amount: float | Decimal,
        currency: str | None = None,
        reason: str = "hold",
        external_ref: str | None = None,
    ) -> Hold:
        """Reserve funds on an account so they can't be spent until released.

        If `currency` is provided and differs from the account currency, the
        amount is converted using the same internal FX table as transfers,
        and the converted amount is what gets held.
        """
        decimal_amount = Decimal(str(amount))
        if decimal_amount <= 0:
            raise InvalidAmount("Amount must be positive")

        account = await self.repository.get_account_for_update(account_id)
        if not account:
            raise AccountNotFound(f"Account {account_id} not found")
        if account.user_id != user_id:
            raise UnauthorizedAccount("Account does not belong to this user")
        if account.is_closed:
            raise AccountClosed("Cannot place a hold on a closed account")

        hold_amount = (
            convert_amount(decimal_amount, currency, account.currency)
            if currency and currency != account.currency
            else decimal_amount
        )

        if account.available_balance < hold_amount:
            raise InsufficientFunds(
                f"Required {hold_amount} {account.currency}, "
                f"available {account.available_balance}"
            )

        account.held_balance += hold_amount
        return await self.repository.create_hold(
            account_id=account.id,
            user_id=user_id,
            amount=hold_amount,
            currency=account.currency,
            reason=reason,
            external_ref=external_ref,
        )

    async def release_hold(self, user_id: UUID, hold_id: UUID) -> Hold:
        """Cancel an active hold — the held funds become spendable again."""
        hold = await self.repository.get_hold_for_update(hold_id)
        if not hold:
            raise HoldNotFound()
        if hold.user_id != user_id:
            raise UnauthorizedAccount("Hold does not belong to this user")
        if hold.status != "active":
            raise HoldAlreadyResolved()

        account = await self.repository.get_account_for_update(hold.account_id)
        if not account:
            raise AccountNotFound(f"Account {hold.account_id} not found")

        account.held_balance -= hold.amount
        if account.held_balance < 0:
            account.held_balance = Decimal("0.0")
        await self.repository.mark_hold_resolved(hold, status="released")
        return hold

    async def get_user_holds(self, user_id: UUID) -> list[Hold]:
        return await self.repository.list_holds_for_user(user_id)

    # ── Account lifecycle ───────────────────────────────────────────────

    async def close_account(self, user_id: UUID, account_id: UUID) -> Account:
        """Close an account. Idempotent — closing an already-closed account
        returns the same row unchanged. Refuses if there's any balance or any
        active holds."""
        account = await self.repository.get_account_for_update(account_id)
        if not account:
            raise AccountNotFound(f"Account {account_id} not found")
        if account.user_id != user_id:
            raise UnauthorizedAccount("Account does not belong to this user")
        if account.is_closed:
            return account
        if account.balance != Decimal("0") or account.held_balance != Decimal("0"):
            raise AccountNotEmpty(
                f"Balance {account.balance} {account.currency}, "
                f"held {account.held_balance} — transfer everything out first"
            )

        account.closed_at = datetime.now(timezone.utc)
        return account
