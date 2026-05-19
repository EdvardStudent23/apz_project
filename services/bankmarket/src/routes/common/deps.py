from __future__ import annotations

from typing import Annotated

from auth_client import CurrentUser, get_current_identity, require_admin
from fastapi import Depends, Header, HTTPException, Request

from src.clients.core_banking import CoreBankingClient
from src.db.repository import MarketRepository
from src.services.market import MarketService
from src.settings import settings


def get_repository(request: Request) -> MarketRepository:
    driver = request.app.state.neo4j_driver
    return MarketRepository(driver)


def get_market_service(
    request: Request,
    repo: Annotated[MarketRepository, Depends(get_repository)],
) -> MarketService:
    banking: CoreBankingClient = request.app.state.core_banking_client
    return MarketService(repo, banking)


async def get_bearer_token(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    return authorization.split(" ", 1)[1]


CurrentIdentity = Annotated[CurrentUser, Depends(get_current_identity)]
AdminIdentity = Annotated[CurrentUser, Depends(require_admin)]
BearerToken = Annotated[str, Depends(get_bearer_token)]


__all__ = [
    "CurrentIdentity",
    "AdminIdentity",
    "BearerToken",
    "get_market_service",
    "settings",
]
