from __future__ import annotations

from typing import Annotated
from uuid import UUID

from common.schemas import ApiResponse
from fastapi import APIRouter, Depends

from src.db.tables import Hold
from src.routes.common.deps import CurrentUser, get_banking_service
from src.routes.schemas import HoldCreate, HoldRead
from src.services.banking import BankingService

router = APIRouter()


def _to_read(hold: Hold) -> HoldRead:
    return HoldRead(
        id=hold.id,
        account_id=hold.account_id,
        amount=float(hold.amount),
        currency=hold.currency,
        reason=hold.reason,
        status=hold.status,
        external_ref=hold.external_ref,
        created_at=hold.created_at,
        resolved_at=hold.resolved_at,
    )


@router.post("/holds", response_model=ApiResponse)
async def place_hold(
    user_id: CurrentUser,
    data: HoldCreate,
    service: Annotated[BankingService, Depends(get_banking_service)],
) -> ApiResponse:
    hold = await service.place_hold(
        user_id=user_id,
        account_id=data.account_id,
        amount=data.amount,
        currency=data.currency,
        reason=data.reason,
        external_ref=data.external_ref,
    )
    await service.repository.session.commit()
    return ApiResponse(status=True, response=_to_read(hold))


@router.post("/holds/{hold_id}/release", response_model=ApiResponse)
async def release_hold(
    user_id: CurrentUser,
    hold_id: UUID,
    service: Annotated[BankingService, Depends(get_banking_service)],
) -> ApiResponse:
    hold = await service.release_hold(user_id=user_id, hold_id=hold_id)
    await service.repository.session.commit()
    return ApiResponse(status=True, response=_to_read(hold))


@router.get("/holds", response_model=ApiResponse)
async def list_holds(
    user_id: CurrentUser,
    service: Annotated[BankingService, Depends(get_banking_service)],
) -> ApiResponse:
    holds = await service.get_user_holds(user_id)
    return ApiResponse(status=True, response=[_to_read(h) for h in holds])
