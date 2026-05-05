from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.repository import BankingRepository
from src.messaging.outbox import OutboxRelay


@pytest.fixture
def session_factory(db_engine):
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_outbox_relay_processing(session_factory, db_session):
    repo = BankingRepository(db_session)
    
    # Create an unprocessed event
    await repo.create_outbox_event(
        event_type="test.event",
        payload={"foo": "bar"}
    )
    await db_session.commit()

    relay = OutboxRelay(
        session_factory=session_factory,
        rabbitmq_url="amqp://guest:guest@localhost:5672/"
    )

    # Mock aio_pika
    with patch("aio_pika.connect_robust", new_callable=AsyncMock) as mock_connect:
        mock_connection = AsyncMock()
        mock_connect.return_value = mock_connection
        
        mock_channel = AsyncMock()
        mock_connection.channel.return_value = mock_channel
        
        mock_exchange = AsyncMock()
        mock_channel.declare_exchange.return_value = mock_exchange

        # Run one processing cycle
        await relay._process_outbox()

        # Verify publication
        assert mock_exchange.publish.called
        args, kwargs = mock_exchange.publish.call_args
        assert kwargs["routing_key"] == "test.event"

        # Verify event marked as processed in DB
        async with session_factory() as session:
            repo_check = BankingRepository(session)
            events = await repo_check.get_unprocessed_outbox_events()
            assert len(events) == 0


@pytest.mark.asyncio
async def test_outbox_relay_error_handling(session_factory):
    relay = OutboxRelay(session_factory, "amqp://...")
    
    with patch("src.messaging.outbox.aio_pika.connect_robust", side_effect=Exception("RabbitMQ Down")):
        # Should not raise exception, just log it
        await relay._process_outbox()


@pytest.mark.asyncio
async def test_outbox_relay_lifecycle(session_factory):
    relay = OutboxRelay(session_factory, "amqp://...")
    
    with patch.object(relay, "_run_loop", new_callable=AsyncMock) as mock_loop:
        await relay.start()
        assert relay._running is True
        assert relay._task is not None
        
        await relay.stop()
        assert relay._running is False
