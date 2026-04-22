"""Legacy runtime ALTERs for pre-Alembic SQLite databases.

Postgres setups use Alembic (see backend/alembic/). This helper stays in place
so that developers with an older SQLite `mni.db` can keep booting without a
manual migration step. It is a no-op on any non-SQLite backend.
"""
from __future__ import annotations

import logging

from sqlalchemy import inspect, text

from .db import engine

log = logging.getLogger("migrate")

REQUIRED_COLUMNS: list[tuple[str, str, str]] = [
    ("users", "last_seen_at", "DATETIME"),
]


def run() -> None:
    if engine.dialect.name != "sqlite":
        return
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
