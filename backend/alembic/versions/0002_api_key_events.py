"""api_key_events table

Revision ID: 0002_api_key_events
Revises: 0001_initial
Create Date: 2026-04-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_api_key_events"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "api_key_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("api_key_id", sa.Integer(), sa.ForeignKey("api_keys.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("ts", sa.DateTime(), nullable=False),
        sa.Column("method", sa.String(length=8), nullable=False),
        sa.Column("path", sa.String(length=256), nullable=False),
        sa.Column("ip", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_api_key_events_api_key_id", "api_key_events", ["api_key_id"])
    op.create_index("ix_api_key_events_user_id", "api_key_events", ["user_id"])
    op.create_index("ix_api_key_events_ts", "api_key_events", ["ts"])


def downgrade() -> None:
    op.drop_table("api_key_events")
