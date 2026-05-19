from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import structlog
from bank_logging import RequestIdMiddleware, configure_logging
from fastapi import FastAPI

from src.clients.core_banking import CoreBankingClient
from src.db.core import make_driver
from src.middleware import ExceptionMiddleware
from src.routes.market import router as market_router
from src.settings import settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings.service_name)

    app.state.neo4j_driver = make_driver()
    app.state.core_banking_client = CoreBankingClient(settings.core_banking_url)

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(settings.auth_jwks_url)
            response.raise_for_status()
            app.state.jwks = response.json()
            logger.info("fetched_jwks", url=settings.auth_jwks_url)
        except Exception as exc:
            logger.error("failed_to_fetch_jwks", error=str(exc))
            app.state.jwks = {"keys": []}

    yield

    await app.state.neo4j_driver.close()


app = FastAPI(title=settings.service_name, lifespan=lifespan)
app.add_middleware(ExceptionMiddleware)
app.add_middleware(RequestIdMiddleware)

app.include_router(market_router)
