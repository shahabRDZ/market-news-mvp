"""Runtime migrations.

SQLAlchemy's create_all only creates missing tables. When we add columns to an
existing table we need to ALTER. This module inspects the DB and applies any
needed additive changes. Idempotent.
"""
from __future__ import annotations

import logging

from sqlalchemy import inspect, text

from .db import engine

log = logging.getLogger("migrate")

# (table, column, SQL fragment after ADD COLUMN)
REQUIRED_COLUMNS: list[tuple[str, str, str]] = [
    ("users", "last_seen_at", "DATETIME"),
]


def run() -> None:
    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())
    with engine.begin() as conn:
        for table, column, ddl in REQUIRED_COLUMNS:
            if table not in existing_tables:
                continue
            cols = {c["name"] for c in insp.get_columns(table)}
            if column in cols:
                continue
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
                log.info("added column %s.%s", table, column)
            except Exception as exc:
                log.warning("failed to add %s.%s: %s", table, column, exc)
