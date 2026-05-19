from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── Products ─────────────────────────────────────────────────────────────


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    price: float = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)


class ProductRead(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    description: str
    price: float
    currency: str
    status: str
    moderation_note: str | None = None
    created_at: datetime


class ModerationDecision(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$")
    note: str | None = Field(default=None, max_length=300)


# ── Orders ───────────────────────────────────────────────────────────────


class OrderCreate(BaseModel):
    product_id: UUID
    account_id: UUID = Field(..., description="The buyer's account to debit / hold from")


class OrderRead(BaseModel):
    id: UUID
    product_id: UUID
    buyer_id: UUID
    hold_id: UUID | None
    amount: float
    currency: str
    status: str
    created_at: datetime
