"""Cross-market contagion: given a large move in asset A in the last 15m,
estimate the historical probability of an aligned move in asset B over the
next 15m / 60m.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import Asset, Candle

PAIRS = [("BTCUSD", "XAUUSD"), ("BTCUSD", "EURUSD"), ("XAUUSD", "EURUSD")]


def _series(db: Session, symbol: str, start: datetime) -> pd.Series:
    a = db.execute(select(Asset).where(Asset.symbol == symbol)).scalar_one_or_none()
    if a is None:
        return pd.Series(dtype=float)
    rows = db.execute(
        select(Candle).where(Candle.asset_id == a.id, Candle.timeframe == "15m", Candle.ts >= start).order_by(Candle.ts.asc())
    ).scalars().all()
    return pd.Series([r.c for r in rows], index=[r.ts for r in rows])


def estimate(db: Session) -> list[dict]:
    now = datetime.utcnow()
    start = now - timedelta(days=7)
    out = []
    for a, b in PAIRS:
        sa, sb = _series(db, a, start), _series(db, b, start)
        if sa.empty or sb.empty:
            continue
        ra, rb = sa.pct_change().dropna(), sb.pct_change().dropna()
        aligned = pd.concat([ra.rename("a"), rb.rename("b")], axis=1, join="inner").dropna()
        if len(aligned) < 40:
            continue
        threshold = aligned["a"].abs().quantile(0.8)
        hits = aligned[aligned["a"].abs() >= threshold]
        if hits.empty:
            continue
        same_sign = ((hits["a"] > 0) == (hits["b"] > 0)).mean()

        # "live" current: last bar of a > threshold?
        last_move = float(ra.iloc[-1]) if len(ra) else 0.0
        active = abs(last_move) >= threshold
        out.append(
            {
                "pair": f"{a}->{b}",
                "threshold_move": round(float(threshold), 5),
                "historical_same_sign_rate": round(float(same_sign), 3),
                "last_move_a": round(last_move, 5),
                "active_trigger": bool(active),
            }
        )
    return out
