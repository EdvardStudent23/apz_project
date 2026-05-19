"""add holds and account.held_balance

Revision ID: 3a7b1f9c2d10
Revises: 224868e01a56
Create Date: 2026-05-19 16:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3a7b1f9c2d10"
down_revision: str | Sequence[str] | None = "224868e01a56"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column(
            "held_balance",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_check_constraint(
        "held_balance_not_negative", "accounts", "held_balance >= 0"
    )
    op.create_check_constraint(
        "held_within_balance", "accounts", "held_balance <= balance"
    )

    op.create_table(
        "holds",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("reason", sa.String(length=120), nullable=False, server_default="hold"),
        sa.Column("external_ref", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount > 0", name="hold_amount_positive"),
        sa.CheckConstraint(
            "status in ('active', 'released', 'completed')",
            name="hold_status_valid",
        ),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_holds_account_id", "holds", ["account_id"])
    op.create_index("ix_holds_user_id", "holds", ["user_id"])
    op.create_index("ix_holds_external_ref", "holds", ["external_ref"])


def downgrade() -> None:
    op.drop_index("ix_holds_external_ref", table_name="holds")
    op.drop_index("ix_holds_user_id", table_name="holds")
    op.drop_index("ix_holds_account_id", table_name="holds")
    op.drop_table("holds")
    op.drop_constraint("held_within_balance", "accounts", type_="check")
    op.drop_constraint("held_balance_not_negative", "accounts", type_="check")
    op.drop_column("accounts", "held_balance")
