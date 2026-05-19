from __future__ import annotations

from typing import Annotated
from uuid import UUID

from bank_logging import bind_contextvars
from common.schemas import ApiResponse
from fastapi import APIRouter, Depends, Request

from src.db.tables import Account
from src.routes.common.deps import CurrentUser, get_banking_service
from src.routes.schemas import (
    AccountCreate,
    AccountRead,
    PublicAccountRead,
    TransactionRead,
    TransferCreate,
)
from src.services.banking import BankingService

router = APIRouter()


def _to_account_read(account: Account) -> AccountRead:
    return AccountRead(
        id=account.id,
        currency=account.currency,
        balance=float(account.balance),
        held_balance=float(account.held_balance),
        available_balance=float(account.available_balance),
        created_at=account.created_at,
        closed_at=account.closed_at,
    )


@router.post("/accounts", response_model=ApiResponse)
async def create_account(
    user_id: CurrentUser,
    data: AccountCreate,
    service: Annotated[BankingService, Depends(get_banking_service)],
) -> ApiResponse:
    account = await service.create_account(user_id, data.currency, data.initial_balance)
    await service.repository.session.commit()
    return ApiResponse(status=True, response=_to_account_read(account))


@router.get("/accounts", response_model=ApiResponse)
async def list_accounts(
    user_id: CurrentUser,
    service: Annotated[BankingService, Depends(get_banking_service)],
) -> ApiResponse:
    accounts = await service.get_user_accounts(user_id)
    return ApiResponse(
        status=True,
        response=[_to_account_read(a) for a in accounts],
    )


@router.post("/accounts/{account_id}/close", response_model=ApiResponse)
async def close_account(
    user_id: CurrentUser,
    account_id: UUID,
    service: Annotated[BankingService, Depends(get_banking_service)],
) -> ApiResponse:
    account = await service.close_account(user_id, account_id)
    await service.repository.session.commit()
    return ApiResponse(status=True, response=_to_account_read(account))


@router.get("/accounts/by-user/{user_id}", response_model=ApiResponse)
async def list_public_accounts_for_user(
    _caller: CurrentUser,
    user_id: str,
    service: Annotated[BankingService, Depends(get_banking_service)],
) -> ApiResponse:
    """List another user's OPEN accounts in a public-safe form (id + currency).

    Used by the 'send to email' flow so the sender can pick which of the
    recipient's accounts to credit. Never returns balance / hold / timestamps.

    `user_id` may be either the int from auth (`9`) or the derived UUID — we
    convert to the canonical UUID either way so it matches what `account.user_id`
    actually stores.
    """
    try:
        target_uuid = UUID(user_id)
    except ValueError:
        try:
            target_uuid = UUID(int=int(user_id))
        except (TypeError, ValueError):
            from fastapi import HTTPException

            raise HTTPException(status_code=400, detail="Invalid user identifier")

    accounts = await service.get_user_accounts(target_uuid)
    return ApiResponse(
        status=True,
        response=[
            PublicAccountRead(id=a.id, currency=a.currency)
            for a in accounts
            if not a.is_closed
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
        user_id=user_id,
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
