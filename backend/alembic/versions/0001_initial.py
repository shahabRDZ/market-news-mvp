"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=64), nullable=False),
        sa.UniqueConstraint("symbol", name="uq_assets_symbol"),
    )
    op.create_index("ix_assets_symbol", "assets", ["symbol"], unique=True)

    op.create_table(
        "news",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("url_hash", sa.String(length=64), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("sentiment", sa.Float(), nullable=False, server_default="0"),
        sa.Column("impact", sa.String(length=8), nullable=False, server_default="LOW"),
        sa.UniqueConstraint("url_hash", name="uq_news_url_hash"),
    )
    op.create_index("ix_news_asset_id", "news", ["asset_id"])
    op.create_index("ix_news_url_hash", "news", ["url_hash"])
    op.create_index("ix_news_published_at", "news", ["published_at"])

    op.create_table(
        "candles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column("ts", sa.DateTime(), nullable=False),
        sa.Column("o", sa.Float(), nullable=False),
        sa.Column("h", sa.Float(), nullable=False),
        sa.Column("l", sa.Float(), nullable=False),
        sa.Column("c", sa.Float(), nullable=False),
        sa.Column("v", sa.Float(), nullable=False),
        sa.UniqueConstraint("asset_id", "timeframe", "ts", name="uq_candle"),
    )
    op.create_index("ix_candles_asset_id", "candles", ["asset_id"])
    op.create_index("ix_candles_ts", "candles", ["ts"])

    op.create_table(
        "signals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("ts", sa.DateTime(), nullable=False),
        sa.Column("direction", sa.String(length=8), nullable=False),
        sa.Column("prob_up", sa.Float(), nullable=False),
        sa.Column("prob_down", sa.Float(), nullable=False),
        sa.Column("prob_neutral", sa.Float(), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=False),
        sa.Column("technical_score", sa.Float(), nullable=False),
        sa.Column("impact_strength", sa.String(length=8), nullable=False),
        sa.Column("reason", sa.String(length=256), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_signals_asset_id", "signals", ["asset_id"])
    op.create_index("ix_signals_ts", "signals", ["ts"])

    op.create_table(
        "economic_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("country", sa.String(length=8), nullable=False),
        sa.Column("importance", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("event_time", sa.DateTime(), nullable=False),
        sa.Column("forecast", sa.Float(), nullable=True),
        sa.Column("previous", sa.Float(), nullable=True),
        sa.Column("actual", sa.Float(), nullable=True),
        sa.Column("affected_assets", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.create_index("ix_economic_events_kind", "economic_events", ["kind"])
    op.create_index("ix_economic_events_country", "economic_events", ["country"])
    op.create_index("ix_economic_events_event_time", "economic_events", ["event_time"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("plan", sa.String(length=32), nullable=False, server_default="free"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "paper_bets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("asset_symbol", sa.String(length=32), nullable=False),
        sa.Column("direction", sa.String(length=8), nullable=False),
        sa.Column("horizon_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("placed_at", sa.DateTime(), nullable=False),
        sa.Column("resolve_at", sa.DateTime(), nullable=False),
        sa.Column("placed_price", sa.Float(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("correct", sa.Boolean(), nullable=True),
        sa.Column("realized_return", sa.Float(), nullable=True),
    )
    op.create_index("ix_paper_bets_user_id", "paper_bets", ["user_id"])
    op.create_index("ix_paper_bets_asset_symbol", "paper_bets", ["asset_symbol"])
    op.create_index("ix_paper_bets_placed_at", "paper_bets", ["placed_at"])
    op.create_index("ix_paper_bets_resolve_at", "paper_bets", ["resolve_at"])

    op.create_table(
        "patterns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_matched_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_patterns_user_id", "patterns", ["user_id"])

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("key_prefix", sa.String(length=12), nullable=False),
        sa.Column("key_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_api_keys_user_id", "api_keys", ["user_id"])
    op.create_index("ix_api_keys_key_prefix", "api_keys", ["key_prefix"])
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"])

    op.create_table(
        "watchlist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "asset_id", name="uq_watch_user_asset"),
    )
    op.create_index("ix_watchlist_user_id", "watchlist", ["user_id"])


def downgrade() -> None:
    op.drop_table("watchlist")
    op.drop_table("api_keys")
    op.drop_table("patterns")
    op.drop_table("paper_bets")
    op.drop_table("users")
    op.drop_table("economic_events")
    op.drop_table("signals")
    op.drop_table("candles")
    op.drop_table("news")
    op.drop_table("assets")
