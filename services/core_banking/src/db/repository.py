from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.tables import Account, OutboxEvent, Transaction


class BankingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_account(self, user_id: UUID, currency: str) -> Account:
        account = Account(user_id=user_id, currency=currency, balance=0.0)
        self.session.add(account)
        await self.session.flush()
        return account

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
