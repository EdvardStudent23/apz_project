from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AccountCreate(BaseModel):
    currency: str = Field(..., min_length=3, max_length=3)
    initial_balance: float = Field(0.0, ge=0)


class AccountRead(BaseModel):
    id: UUID
    currency: str
    balance: float
    held_balance: float = 0.0
    available_balance: float = 0.0
    created_at: datetime
    closed_at: datetime | None = None


class PublicAccountRead(BaseModel):
    """Public-safe slice of an account, returned when someone looks up
    accounts they don't own (e.g. to pick a recipient account). Never
    leaks balance, hold, or timestamps beyond the open/closed flag."""

    id: UUID
    currency: str


class TransferCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sender_account_id: UUID = Field(..., alias="from_account_id")
    receiver_account_id: UUID = Field(..., alias="to_account_id")
    amount: float = Field(..., gt=0)
    purpose: str | None = None


class TransactionRead(BaseModel):
    id: UUID
    sender_account_id: UUID
    receiver_account_id: UUID
    amount: float
    currency: str
    purpose: str | None
    created_at: datetime


class HoldCreate(BaseModel):
    """Body for `POST /holds`. Either currency=None (hold in the account's
    own currency) or currency=<ISO code> for the requested amount, in which
    case the service converts to the account currency at internal rates."""

    account_id: UUID
    amount: float = Field(..., gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    reason: str = Field(default="hold", min_length=1, max_length=120)
    external_ref: str | None = Field(default=None, max_length=128)


class HoldRead(BaseModel):
    id: UUID
    account_id: UUID
    amount: float
    currency: str
    reason: str
    status: str
    external_ref: str | None
    created_at: datetime
    resolved_at: datetime | None = None
