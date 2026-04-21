"""Time-machine snapshot: reconstruct mood / signal / news as of a past timestamp."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import Asset, News, Signal


def snapshot_signals(db: Session, as_of: datetime) -> list[dict]:
    assets = db.execute(select(Asset)).scalars().all()
    out: list[dict] = []
    for a in assets:
        last = db.execute(
            select(Signal).where(Signal.asset_id == a.id, Signal.ts <= as_of).order_by(Signal.ts.desc()).limit(1)
        ).scalar_one_or_none()
        if last is None:
            continue
        out.append(
            {
                "asset": a.symbol,
                "ts": last.ts.isoformat() + "Z",
                "direction": last.direction,
                "probabilities": {"up": last.prob_up, "down": last.prob_down, "neutral": last.prob_neutral},
                "sentiment_score": last.sentiment_score,
                "technical_score": last.technical_score,
                "impact_strength": last.impact_strength,
                "reason": last.reason,
            }
        )
    return out


def snapshot_news(db: Session, as_of: datetime, hours: int = 6, limit: int = 20) -> list[dict]:
    cutoff = as_of - timedelta(hours=hours)
    rows = db.execute(
        select(News).where(News.published_at >= cutoff, News.published_at <= as_of).order_by(News.published_at.desc()).limit(limit)
    ).scalars().all()
    return [
        {
            "id": r.id,
            "source": r.source,
            "title": r.title,
            "url": r.url,
            "published_at": r.published_at.isoformat() + "Z",
            "sentiment": r.sentiment,
            "impact": r.impact,
        }
        for r in rows
    ]
