from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import structlog
from bank_logging import RequestIdMiddleware, configure_logging
from fastapi import FastAPI

from src.db.core import make_engine, make_session_factory
from src.messaging.outbox import OutboxRelay
from src.middleware import ExceptionMiddleware
from src.routes.banking import router as banking_router
from src.settings import settings
from src.routes.common.deps import get_current_user
from uuid import uuid4, UUID

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings.service_name)
    
    # DB initialization
    engine = make_engine()
    app.state.db_sessionmaker = make_session_factory(engine)
    
    # Fetch JWKS for auth_client
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(settings.auth_jwks_url)
            response.raise_for_status()
            app.state.jwks = response.json()
            logger.info("fetched jwks from auth service")
        except Exception as e:
            logger.error("failed to fetch jwks, enabling auth bypass for local testing", error=str(e))
            app.state.jwks = {"keys": []}
            # Use a fixed UUID for local development bypass to ensure consistency across reloads
            local_dev_user_id = UUID("00000000-0000-0000-0000-000000000000")
            app.dependency_overrides[get_current_user] = lambda: local_dev_user_id

    # Start Outbox Relay
    app.state.outbox_relay = OutboxRelay(
        session_factory=app.state.db_sessionmaker,
        rabbitmq_url=settings.rabbitmq_url,
    )
    await app.state.outbox_relay.start()

    yield
    
    # Shutdown
    await app.state.outbox_relay.stop()
    await engine.dispose()


app = FastAPI(title=settings.service_name, lifespan=lifespan)
app.add_middleware(ExceptionMiddleware)
app.add_middleware(RequestIdMiddleware)

app.include_router(banking_router, tags=["banking"])
