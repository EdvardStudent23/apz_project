from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from auth_client.jwt import get_current_user
from src.db.repository import BankingRepository
from src.services.banking import BankingService


async def get_db_session(request: Request) -> AsyncSession:
    async with request.app.state.db_sessionmaker() as session:
        yield session


async def get_banking_service(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> BankingService:
    repo = BankingRepository(session)
    return BankingService(repo)


CurrentUser = Annotated[UUID, Depends(get_current_user)]
