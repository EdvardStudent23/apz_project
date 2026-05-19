"""add accounts.closed_at

Revision ID: 4d8c2e1a7b30
Revises: 3a7b1f9c2d10
Create Date: 2026-05-19 17:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4d8c2e1a7b30"
down_revision: str | Sequence[str] | None = "3a7b1f9c2d10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("accounts", "closed_at")
