"""Reliability / calibration dashboard.

For each past signal, look up the realized return over the next `horizon`
candles. Bin by the probability assigned to the predicted direction. Compare
the empirical hit-rate per bin to the bin midpoint (the ideal reliability line).
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import Asset, Candle, Signal

BINS = [(0.0, 0.4), (0.4, 0.55), (0.55, 0.7), (0.7, 0.85), (0.85, 1.01)]


def _candle_series(db: Session, asset_id: int) -> pd.Series:
    rows = db.execute(
        select(Candle).where(Candle.asset_id == asset_id, Candle.timeframe == "15m").order_by(Candle.ts.asc())
    ).scalars().all()
    if not rows:
        return pd.Series(dtype=float)
    return pd.Series([r.c for r in rows], index=[r.ts for r in rows])


def _realized_return(series: pd.Series, anchor: datetime, horizon_min: int) -> float | None:
    if series.empty:
        return None
    before = series[series.index <= anchor]
    after = series[series.index >= anchor + timedelta(minutes=horizon_min)]
    if before.empty or after.empty:
        return None
    return float((after.iloc[0] - before.iloc[-1]) / before.iloc[-1])


def compute(db: Session, horizon_min: int = 60, days: int = 30) -> dict:
    cutoff = datetime.utcnow() - timedelta(days=days)
    assets = db.execute(select(Asset)).scalars().all()
    buckets: list[list[tuple[float, bool]]] = [[] for _ in BINS]
    total = 0

    for a in assets:
        series = _candle_series(db, a.id)
        sigs = db.execute(
            select(Signal).where(Signal.asset_id == a.id, Signal.ts >= cutoff).order_by(Signal.ts.asc())
        ).scalars().all()
        for sig in sigs:
            if sig.direction == "NEUTRAL":
                continue
            rr = _realized_return(series, sig.ts, horizon_min)
            if rr is None:
                continue
            prob = sig.prob_up if sig.direction == "UP" else sig.prob_down
            hit = (rr > 0 and sig.direction == "UP") or (rr < 0 and sig.direction == "DOWN")
            for i, (lo, hi) in enumerate(BINS):
                if lo <= prob < hi:
                    buckets[i].append((prob, hit))
                    total += 1
                    break

    curve = []
    for (lo, hi), entries in zip(BINS, buckets):
        if not entries:
            curve.append({"bin": f"{int(lo*100)}-{int(hi*100)}%", "count": 0, "hit_rate": None, "ideal": round((lo + hi) / 2, 2)})
            continue
        hits = sum(1 for _, h in entries if h)
        curve.append(
            {
                "bin": f"{int(lo*100)}-{int(hi*100)}%",
                "count": len(entries),
                "hit_rate": round(hits / len(entries), 3),
                "ideal": round((lo + hi) / 2, 2),
            }
        )

    # Brier score proxy over non-neutral preds.
    brier_entries = [p for entries in buckets for p in entries]
    brier = (
        round(sum((p - (1.0 if h else 0.0)) ** 2 for p, h in brier_entries) / len(brier_entries), 4)
        if brier_entries
        else None
    )

    return {"horizon_min": horizon_min, "days": days, "total": total, "curve": curve, "brier": brier}
