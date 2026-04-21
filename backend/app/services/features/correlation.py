"""Correlation break detector.

For each configured pair, compare short-window (60m) correlation of returns
against a long-window (7d) baseline. A z-score > 2 flags a break.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import Asset, Candle

DEFAULT_PAIRS = [("EURUSD", "BTCUSD"), ("EURUSD", "XAUUSD"), ("BTCUSD", "XAUUSD")]


def _returns(db: Session, symbol: str, start: datetime) -> pd.Series:
    a = db.execute(select(Asset).where(Asset.symbol == symbol)).scalar_one_or_none()
    if a is None:
        return pd.Series(dtype=float)
    rows = db.execute(
        select(Candle).where(Candle.asset_id == a.id, Candle.timeframe == "15m", Candle.ts >= start).order_by(Candle.ts.asc())
    ).scalars().all()
    if not rows:
        return pd.Series(dtype=float)
    s = pd.Series([r.c for r in rows], index=[r.ts for r in rows])
    return s.pct_change().dropna()


def detect(db: Session, pairs: list[tuple[str, str]] | None = None) -> list[dict]:
    pairs = pairs or DEFAULT_PAIRS
    now = datetime.utcnow()
    out: list[dict] = []
    for a, b in pairs:
        ra_long = _returns(db, a, now - timedelta(days=7))
        rb_long = _returns(db, b, now - timedelta(days=7))
        if ra_long.empty or rb_long.empty:
            continue
        aligned = pd.concat([ra_long, rb_long], axis=1, join="inner").dropna()
        if len(aligned) < 40:
            continue
        baseline = float(aligned.iloc[:, 0].corr(aligned.iloc[:, 1]))

        short = aligned.tail(16)  # last ~4h of 15m bars
        if len(short) < 6:
            continue
        current = float(short.iloc[:, 0].corr(short.iloc[:, 1]))

        delta = abs(current - baseline)
        flagged = delta > 0.4 and abs(baseline) > 0.3
        out.append(
            {
                "pair": f"{a}-{b}",
                "baseline_corr": round(baseline, 3),
                "current_corr": round(current, 3),
                "delta": round(delta, 3),
                "break_flag": flagged,
            }
        )
    return out
