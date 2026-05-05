from __future__ import annotations

from typing import Annotated

from bank_logging import bind_contextvars
from common.schemas import ApiResponse
from fastapi import APIRouter, Depends, Request

from src.routes.common.deps import CurrentUser, get_banking_service
from src.routes.schemas import (
    AccountCreate,
    AccountRead,
    TransactionRead,
    TransferCreate,
)
from src.services.banking import BankingService

router = APIRouter()


@router.post("/accounts", response_model=ApiResponse)
async def create_account(
    user_id: CurrentUser,
    data: AccountCreate,
    service: Annotated[BankingService, Depends(get_banking_service)],
) -> ApiResponse:
    account = await service.create_account(user_id, data.currency)
    await service.repository.session.commit()
    return ApiResponse(
        status=True,
        response=AccountRead(
            id=account.id,
            currency=account.currency,
            balance=float(account.balance),
            created_at=account.created_at,
        ),
    )


@router.get("/accounts", response_model=ApiResponse)
async def list_accounts(
    user_id: CurrentUser,
    service: Annotated[BankingService, Depends(get_banking_service)],
) -> ApiResponse:
    accounts = await service.get_user_accounts(user_id)
    return ApiResponse(
        status=True,
        response=[
            AccountRead(
                id=a.id,
                currency=a.currency,
                balance=float(a.balance),
                created_at=a.created_at,
            )
            for a in accounts
        ],
    )


@router.post("/transfers", response_model=ApiResponse)
async def transfer_money(
    user_id: CurrentUser,
    data: TransferCreate,
    request: Request,
    service: Annotated[BankingService, Depends(get_banking_service)],
) -> ApiResponse:
    request_id = request.headers.get("x-request-id")
    bind_contextvars(user_id=str(user_id), request_id=request_id)

    transaction = await service.transfer_money(
        sender_account_id=data.sender_account_id,
        receiver_account_id=data.receiver_account_id,
        amount=data.amount,
        purpose=data.purpose,
        request_id=request_id,
    )
    await service.repository.session.commit()

    return ApiResponse(
        status=True,
        response=TransactionRead(
            id=transaction.id,
            sender_account_id=transaction.sender_account_id,
            receiver_account_id=transaction.receiver_account_id,
            amount=float(transaction.amount),
            currency=transaction.currency,
            purpose=transaction.purpose,
            created_at=transaction.created_at,
        ),
    )
