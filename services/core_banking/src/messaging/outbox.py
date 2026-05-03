from __future__ import annotations

import asyncio
from datetime import datetime, UTC
from uuid import uuid4

import aio_pika
import structlog
from sqlalchemy.ext.asyncio import async_sessionmaker

from messaging.envelope import EventEnvelope
from src.db.repository import BankingRepository
from src.settings import settings

logger = structlog.get_logger(__name__)


class OutboxRelay:
    def __init__(
        self,
        session_factory: async_sessionmaker,
        rabbitmq_url: str,
        exchange_name: str = "core_banking.events",
    ) -> None:
        self.session_factory = session_factory
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("outbox relay started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            await self._task
        logger.info("outbox relay stopped")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self._process_outbox()
            except Exception as e:
                logger.error("outbox relay error", error=str(e))
            
            await asyncio.sleep(1.0)  # Poll every second

    async def _process_outbox(self) -> None:
        try:
            connection = await aio_pika.connect_robust(self.rabbitmq_url)
        except Exception as e:
            logger.error("failed to connect to rabbitmq", error=str(e))
            return

        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange(
                self.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
            )

            async with self.session_factory() as session:
                repo = BankingRepository(session)
                events = await repo.get_unprocessed_outbox_events(limit=50)
                
                if not events:
                    return

                for event in events:
                    envelope = EventEnvelope(
                        event_id=str(event.id),
                        event_type=event.event_type,
                        occurred_at=event.created_at,
                        producer=settings.service_name,
                        payload=event.payload,
                    )

                    message = aio_pika.Message(
                        body=envelope.model_dump_json().encode(),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    )

                    await exchange.publish(
                        message, routing_key=event.event_type
                    )
                    
                    await repo.mark_outbox_event_processed(event.id)
                    logger.info(
                        "event published from outbox",
                        event_id=event.id,
                        event_type=event.event_type,
                    )

                await session.commit()
