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
    created_at: datetime


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
