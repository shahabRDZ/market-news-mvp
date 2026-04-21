"""'Did I miss anything' digest since the user's last_seen_at."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import Asset, News, Signal, User


def build(db: Session, user: User) -> dict:
    last_seen = user.last_seen_at or (datetime.utcnow() - timedelta(hours=2))
    now = datetime.utcnow()
    gap_minutes = int((now - last_seen).total_seconds() / 60)

    news_rows = (
        db.execute(
            select(News).where(News.published_at >= last_seen).order_by(News.impact.desc(), News.published_at.desc()).limit(5)
        )
        .scalars()
        .all()
    )

    direction_changes: list[dict] = []
    assets = db.execute(select(Asset)).scalars().all()
    for a in assets:
        before = db.execute(
            select(Signal).where(Signal.asset_id == a.id, Signal.ts <= last_seen).order_by(Signal.ts.desc()).limit(1)
        ).scalar_one_or_none()
        after = db.execute(
            select(Signal).where(Signal.asset_id == a.id).order_by(Signal.ts.desc()).limit(1)
        ).scalar_one_or_none()
        if before and after and before.direction != after.direction:
            direction_changes.append(
                {
                    "asset": a.symbol,
                    "from": before.direction,
                    "to": after.direction,
                    "new_probability": max(after.prob_up, after.prob_down, after.prob_neutral),
                }
            )

    return {
        "last_seen": last_seen.isoformat() + "Z",
        "gap_minutes": gap_minutes,
        "high_impact_count": sum(1 for n in news_rows if n.impact == "HIGH"),
        "news": [
            {"title": n.title, "impact": n.impact, "sentiment": n.sentiment, "source": n.source, "id": n.id}
            for n in news_rows
        ],
        "direction_changes": direction_changes,
    }


def touch(db: Session, user: User) -> None:
    user.last_seen_at = datetime.utcnow()
    db.add(user)
    db.commit()
