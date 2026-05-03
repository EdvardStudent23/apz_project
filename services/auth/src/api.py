from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from bank_logging import RequestIdMiddleware, configure_logging
from fastapi import FastAPI

from src.middleware import ExceptionMiddleware
from src.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging(settings.service_name)
    yield


app = FastAPI(title=settings.service_name, lifespan=lifespan)
app.add_middleware(ExceptionMiddleware)
app.add_middleware(RequestIdMiddleware)
