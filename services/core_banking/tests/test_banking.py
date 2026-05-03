from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repository import BankingRepository
from src.services.banking import BankingService
from src.services.exceptions import (
    AccountNotFound,
    CurrencyMismatch,
    InsufficientFunds,
    InvalidAmount,
)


@pytest.fixture
def banking_service(db_session: AsyncSession):
    repo = BankingRepository(db_session)
    return BankingService(repo)


@pytest.mark.asyncio
async def test_create_account(banking_service: BankingService):
    user_id = uuid4()
    account = await banking_service.create_account(user_id, "USD")
    
    assert account.user_id == user_id
    assert account.currency == "USD"
    assert account.balance == 0.0


@pytest.mark.asyncio
async def test_get_user_accounts(banking_service: BankingService):
    user_id = uuid4()
    await banking_service.create_account(user_id, "USD")
    await banking_service.create_account(user_id, "EUR")
    
    accounts = await banking_service.get_user_accounts(user_id)
    assert len(accounts) == 2
    assert {a.currency for a in accounts} == {"USD", "EUR"}


@pytest.mark.asyncio
async def test_successful_transfer(banking_service: BankingService):
    user1 = uuid4()
    user2 = uuid4()
    
    acc1 = await banking_service.create_account(user1, "USD")
    acc2 = await banking_service.create_account(user2, "USD")
    
    # Manually set balance for test
    acc1.balance = 100.0
    await banking_service.repository.session.flush()

    tx = await banking_service.transfer_money(
        sender_account_id=acc1.id,
        receiver_account_id=acc2.id,
        amount=40.0,
        purpose="Test transfer"
    )
    
    assert tx.amount == 40.0
    assert acc1.balance == 60.0
    assert acc2.balance == 40.0
    
    # Check outbox
    events = await banking_service.repository.get_unprocessed_outbox_events()
    assert len(events) == 1
    assert events[0].event_type == "transaction.created"
    assert events[0].payload["transaction_id"] == str(tx.id)


@pytest.mark.asyncio
async def test_transfer_invalid_amount(banking_service: BankingService):
    acc1_id = uuid4()
    acc2_id = uuid4()
    
    with pytest.raises(InvalidAmount):
        await banking_service.transfer_money(acc1_id, acc2_id, -10.0)
    
    with pytest.raises(InvalidAmount):
        await banking_service.transfer_money(acc1_id, acc2_id, 0.0)


@pytest.mark.asyncio
async def test_transfer_account_not_found(banking_service: BankingService):
    user_id = uuid4()
    acc1 = await banking_service.create_account(user_id, "USD")
    
    with pytest.raises(AccountNotFound):
        await banking_service.transfer_money(acc1.id, uuid4(), 10.0)
    
    with pytest.raises(AccountNotFound):
        await banking_service.transfer_money(uuid4(), acc1.id, 10.0)


@pytest.mark.asyncio
async def test_transfer_currency_mismatch(banking_service: BankingService):
    user1 = uuid4()
    user2 = uuid4()
    
    acc1 = await banking_service.create_account(user1, "USD")
    acc2 = await banking_service.create_account(user2, "EUR")
    
    with pytest.raises(CurrencyMismatch):
        await banking_service.transfer_money(acc1.id, acc2.id, 10.0)


@pytest.mark.asyncio
async def test_transfer_insufficient_funds(banking_service: BankingService):
    user1 = uuid4()
    user2 = uuid4()
    
    acc1 = await banking_service.create_account(user1, "USD")
    acc2 = await banking_service.create_account(user2, "USD")
    
    acc1.balance = 5.0
    await banking_service.repository.session.flush()

    with pytest.raises(InsufficientFunds):
        await banking_service.transfer_money(acc1.id, acc2.id, 10.0)
