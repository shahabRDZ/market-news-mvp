"""Silence detector: compare news rate over last 30m vs the baseline for the
same hour-of-day over the past 7 days.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import News


def detect(db: Session) -> dict:
    now = datetime.utcnow()
    window = timedelta(minutes=30)

    recent_count = len(
        db.execute(
            select(News).where(News.published_at >= now - window)
        )
        .scalars()
        .all()
    )

    baseline_counts: list[int] = []
    for day in range(1, 8):
        anchor = now - timedelta(days=day)
        baseline_counts.append(
            len(
                db.execute(
                    select(News).where(
                        News.published_at >= anchor - window,
                        News.published_at <= anchor,
                    )
                )
                .scalars()
                .all()
            )
        )
    baseline = sum(baseline_counts) / max(1, len(baseline_counts))

    if baseline < 2:
        return {"silent": False, "recent": recent_count, "baseline": round(baseline, 1), "note": "not enough history"}

    ratio = recent_count / baseline
    silent = ratio <= 0.4 and baseline >= 3
    return {
        "silent": silent,
        "recent": recent_count,
        "baseline": round(baseline, 1),
        "ratio": round(ratio, 2),
        "note": "Unusual silence; news desk may be sitting on something" if silent else "normal news flow",
    }
