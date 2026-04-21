"""News-reaction replay engine.

Given a news item, find similar past items by (sentiment sign, impact class,
keyword overlap) and report the realized return buckets that followed in the
next 15m / 1h / 4h windows.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import Candle, News


@dataclass
class ReplayOutcome:
    news_id: int
    title: str
    published_at: str
    similarity: float
    ret_15m: float | None
    ret_1h: float | None
    ret_4h: float | None


def _tokens(text: str) -> set[str]:
    return {t.lower().strip(".,:;!?") for t in text.split() if len(t) > 3}


def _similarity(a: News, b: News) -> float:
    sent_match = 1.0 if (a.sentiment > 0) == (b.sentiment > 0) else 0.0
    impact_match = 1.0 if a.impact == b.impact else 0.5
    overlap = _tokens(a.title) & _tokens(b.title)
    lex = min(1.0, len(overlap) / 4.0)
    return round(0.3 * sent_match + 0.3 * impact_match + 0.4 * lex, 3)


def _return_at(candles: pd.Series, anchor_ts, minutes: int) -> float | None:
    if candles.empty or anchor_ts is None:
        return None
    before = candles[candles.index <= anchor_ts]
    after = candles[candles.index >= anchor_ts + timedelta(minutes=minutes)]
    if before.empty or after.empty:
        return None
    return round(float((after.iloc[0] - before.iloc[-1]) / before.iloc[-1]), 5)


def replay_for(db: Session, target: News, asset_id: int, limit: int = 5) -> list[ReplayOutcome]:
    past = (
        db.execute(
            select(News)
            .where(News.asset_id == asset_id, News.id != target.id)
            .order_by(News.published_at.desc())
            .limit(300)
        )
        .scalars()
        .all()
    )
    scored = sorted(
        ((_similarity(target, p), p) for p in past),
        key=lambda x: x[0],
        reverse=True,
    )[:limit]

    candle_rows = (
        db.execute(
            select(Candle).where(Candle.asset_id == asset_id, Candle.timeframe == "15m").order_by(Candle.ts.asc())
        )
        .scalars()
        .all()
    )
    series = pd.Series([r.c for r in candle_rows], index=[r.ts for r in candle_rows])

    outcomes: list[ReplayOutcome] = []
    for sim, p in scored:
        if sim <= 0.2:
            continue
        outcomes.append(
            ReplayOutcome(
                news_id=p.id,
                title=p.title,
                published_at=p.published_at.isoformat() + "Z",
                similarity=sim,
                ret_15m=_return_at(series, p.published_at, 15),
                ret_1h=_return_at(series, p.published_at, 60),
                ret_4h=_return_at(series, p.published_at, 240),
            )
        )
    return outcomes
