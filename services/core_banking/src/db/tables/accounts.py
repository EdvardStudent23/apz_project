from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from decimal import Decimal
from sqlalchemy import CheckConstraint, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(index=True, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(20, 2), nullable=False, default=Decimal("0.0")
    )
    held_balance: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0.0"),
        server_default="0",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        CheckConstraint("balance >= 0", name="balance_not_negative"),
        CheckConstraint("held_balance >= 0", name="held_balance_not_negative"),
        CheckConstraint("held_balance <= balance", name="held_within_balance"),
    )

    @property
    def is_closed(self) -> bool:
        return self.closed_at is not None

    @property
    def available_balance(self) -> Decimal:
        balance = self.balance if isinstance(self.balance, Decimal) else Decimal(str(self.balance))
        held = self.held_balance if isinstance(self.held_balance, Decimal) else Decimal(str(self.held_balance))
        return balance - held
