from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.core import Base


class Hold(Base):
    """A reservation of funds on an account.

    A hold increments the owning account's `held_balance`, lowering its
    available balance. The held amount is later released (decrementing
    `held_balance` only) or completed (decrementing both `held_balance` and
    `balance`, and crediting a destination account elsewhere).
    """

    __tablename__ = "holds"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(index=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    reason: Mapped[str] = mapped_column(String(120), nullable=False, default="hold")
    external_ref: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active", server_default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="hold_amount_positive"),
        CheckConstraint(
            "status in ('active', 'released', 'completed')",
            name="hold_status_valid",
        ),
    )
