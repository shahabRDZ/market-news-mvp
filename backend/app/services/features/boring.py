"""Boring day detector.

Composite: low news rate + low realized volatility + no Tier-1 event in next 4h.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import Asset, Candle, EconomicEvent, News


def assess(db: Session) -> dict:
    now = datetime.utcnow()

    news_count = len(
        db.execute(select(News).where(News.published_at >= now - timedelta(hours=4))).scalars().all()
    )

    vols: list[float] = []
    for a in db.execute(select(Asset)).scalars().all():
        rows = db.execute(
            select(Candle).where(Candle.asset_id == a.id, Candle.timeframe == "15m", Candle.ts >= now - timedelta(hours=4)).order_by(Candle.ts.asc())
        ).scalars().all()
        if len(rows) >= 5:
            s = pd.Series([r.c for r in rows])
            vols.append(float(s.pct_change().std() or 0.0))
    avg_vol = sum(vols) / len(vols) if vols else 0.0

    tier1 = db.execute(
        select(EconomicEvent).where(
            EconomicEvent.importance >= 3,
            EconomicEvent.event_time >= now,
            EconomicEvent.event_time <= now + timedelta(hours=4),
        )
    ).scalars().all()

    score = 0
    if news_count <= 3:
        score += 40
    elif news_count <= 6:
        score += 20
    if avg_vol <= 0.0005:
        score += 40
    elif avg_vol <= 0.001:
        score += 20
    if not tier1:
        score += 20
    boring = score >= 70

    note = (
        "Calm, low news flow, no tier-1 events ahead. Overtrading here usually loses."
        if boring
        else "Active tape, stay engaged."
    )
    return {
        "score": score,
        "boring": boring,
        "recent_news_4h": news_count,
        "avg_realized_vol": round(avg_vol, 6),
        "tier1_events_next_4h": len(tier1),
        "note": note,
    }
