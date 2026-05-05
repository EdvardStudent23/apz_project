from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    currency: str = Field(..., min_length=3, max_length=3)


class AccountRead(BaseModel):
    id: UUID
    currency: str
    balance: float
    created_at: datetime


class TransferCreate(BaseModel):
    sender_account_id: UUID
    receiver_account_id: UUID
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
