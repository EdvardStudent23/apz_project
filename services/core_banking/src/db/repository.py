from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.tables import Account, Hold, OutboxEvent, Transaction


class BankingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_account(self, user_id: UUID, currency: str, initial_balance: float = 0.0) -> Account:
        account = Account(user_id=user_id, currency=currency, balance=initial_balance)
        self.session.add(account)
        await self.session.flush()
        return account

    # ── Holds ────────────────────────────────────────────────────────────

    async def create_hold(
        self,
        account_id: UUID,
        user_id: UUID,
        amount: Decimal,
        currency: str,
        reason: str,
        external_ref: str | None,
    ) -> Hold:
        hold = Hold(
            account_id=account_id,
            user_id=user_id,
            amount=amount,
            currency=currency,
            reason=reason,
            external_ref=external_ref,
        )
        self.session.add(hold)
        await self.session.flush()
        return hold

    async def get_hold_for_update(self, hold_id: UUID) -> Hold | None:
        stmt = select(Hold).where(Hold.id == hold_id).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_holds_for_account(self, account_id: UUID) -> list[Hold]:
        stmt = (
            select(Hold)
            .where(Hold.account_id == account_id)
            .order_by(Hold.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_holds_for_user(self, user_id: UUID) -> list[Hold]:
        stmt = (
            select(Hold)
            .where(Hold.user_id == user_id)
            .order_by(Hold.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_hold_resolved(self, hold: Hold, status: str) -> None:
        hold.status = status
        hold.resolved_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def get_accounts_by_user(self, user_id: UUID) -> list[Account]:
        stmt = select(Account).where(Account.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_account_for_update(self, account_id: UUID) -> Account | None:
        """Fetch an account and lock the row for update."""
        stmt = select(Account).where(Account.id == account_id).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_transaction(
        self,
        sender_id: UUID,
        receiver_id: UUID,
        amount: float,
        currency: str,
        purpose: str | None = None,
        request_id: str | None = None,
    ) -> Transaction:
        transaction = Transaction(
            sender_account_id=sender_id,
            receiver_account_id=receiver_id,
            amount=amount,
            currency=currency,
            purpose=purpose,
            request_id=request_id,
        )
        self.session.add(transaction)
        await self.session.flush()
        return transaction

    async def create_outbox_event(self, event_type: str, payload: dict) -> OutboxEvent:
        event = OutboxEvent(event_type=event_type, payload=payload)
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_unprocessed_outbox_events(self, limit: int = 100) -> list[OutboxEvent]:
        stmt = (
            select(OutboxEvent)
            .where(OutboxEvent.processed == False)
            .order_by(OutboxEvent.created_at)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_outbox_event_processed(self, event_id: UUID) -> None:
        stmt = select(OutboxEvent).where(OutboxEvent.id == event_id)
        result = await self.session.execute(stmt)
        event = result.scalar_one_or_none()
        if event:
            event.processed = True
            await self.session.flush()
