"""Retail vs institutional sentiment split.

Source classification table is simple enough to stay static. Once we add
Reddit/Twitter ingestion those land in `retail` automatically.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import News

INSTITUTIONAL = {"reuters", "bloomberg", "financial times", "ft", "wall street journal", "wsj", "dow jones"}
RETAIL = {"reddit", "twitter", "stocktwits", "seeking alpha", "youtube"}


def _classify(source: str) -> str:
    s = source.lower()
    if any(k in s for k in INSTITUTIONAL):
        return "institutional"
    if any(k in s for k in RETAIL):
        return "retail"
    return "mixed"


def split(db: Session, hours: int = 24) -> dict:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    rows = db.execute(select(News).where(News.published_at >= cutoff)).scalars().all()
    buckets: dict[str, list[float]] = {"institutional": [], "retail": [], "mixed": []}
    for r in rows:
        buckets[_classify(r.source)].append(r.sentiment)

    summary = {}
    for k, vals in buckets.items():
        summary[k] = {
            "count": len(vals),
            "mean_sentiment": round(sum(vals) / len(vals), 3) if vals else 0.0,
        }

    retail_mean = summary["retail"]["mean_sentiment"]
    inst_mean = summary["institutional"]["mean_sentiment"]
    divergence = round(retail_mean - inst_mean, 3)
    flag = "RETAIL_EUPHORIA" if retail_mean > 0.3 and inst_mean < 0 else (
        "RETAIL_CAPITULATION" if retail_mean < -0.3 and inst_mean > 0 else "ALIGNED"
    )
    return {"window_hours": hours, "groups": summary, "divergence": divergence, "flag": flag}
