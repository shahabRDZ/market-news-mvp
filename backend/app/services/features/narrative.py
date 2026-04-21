"""Narrative tracking: pick high-signal keyword n-grams from recent news and
compare current-week frequency to prior-week frequency. Emerging narratives are
those whose frequency ratio crosses a threshold.
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import News

STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "into", "after", "over",
    "amid", "says", "said", "new", "news", "update", "top", "more", "as", "by",
    "to", "of", "in", "on", "a", "an", "is", "are", "was", "were", "be", "will",
    "has", "have", "had", "us", "eu", "uk",
}


def _tokens(s: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[A-Za-z]{4,}", s) if w.lower() not in STOPWORDS]


def _ngrams(tokens: list[str], n: int = 2) -> list[str]:
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def detect(db: Session, window_days: int = 7, top: int = 6) -> list[dict]:
    now = datetime.utcnow()
    cur_start = now - timedelta(days=window_days)
    prev_start = now - timedelta(days=window_days * 2)
    rows = db.execute(
        select(News).where(News.published_at >= prev_start).order_by(News.published_at.desc())
    ).scalars().all()
    cur, prev = Counter(), Counter()
    for r in rows:
        grams = _ngrams(_tokens(r.title), 2) + _tokens(r.title)
        bucket = cur if r.published_at >= cur_start else prev
        for g in grams:
            bucket[g] += 1
    out = []
    for term, cur_count in cur.most_common(60):
        prev_count = prev.get(term, 0)
        if cur_count < 3:
            continue
        ratio = cur_count / max(1, prev_count)
        trend = "↑" if ratio >= 1.5 else ("↓" if ratio <= 0.6 else "→")
        out.append({"term": term, "current": cur_count, "previous": prev_count, "ratio": round(ratio, 2), "trend": trend})
    out.sort(key=lambda x: (x["trend"] == "↑", x["ratio"]), reverse=True)
    return out[:top]
