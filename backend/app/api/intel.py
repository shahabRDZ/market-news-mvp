from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Asset, Candle, EconomicEvent, News
from ..services.advanced import contradiction, countdown, liquidity, replay, smart_money, stress
from ..services.events_fetcher import anticipation_pressure

router = APIRouter(prefix="/intel", tags=["intel"])


def _load_ohlcv_df(db: Session, asset_id: int, timeframe: str = "15m", limit: int = 400) -> pd.DataFrame:
    rows = (
        db.execute(
            select(Candle)
            .where(Candle.asset_id == asset_id, Candle.timeframe == timeframe)
            .order_by(Candle.ts.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    rows = sorted(rows, key=lambda r: r.ts)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(
        [{"o": r.o, "h": r.h, "l": r.l, "c": r.c, "v": r.v} for r in rows],
        index=[r.ts for r in rows],
    )


def _next_event_for(db: Session, symbol: str) -> EconomicEvent | None:
    now = datetime.utcnow()
    rows = (
        db.execute(
            select(EconomicEvent)
            .where(EconomicEvent.event_time >= now, EconomicEvent.importance >= 2)
            .order_by(EconomicEvent.event_time.asc())
            .limit(20)
        )
        .scalars()
        .all()
    )
    for r in rows:
        assets = r.affected_assets or []
        if symbol in assets or symbol[:3] in assets or symbol[3:] in assets:
            return r
    return rows[0] if rows else None


def _sentiment_last_6h(db: Session, asset_id: int) -> float:
    cutoff = datetime.utcnow() - timedelta(hours=6)
    rows = (
        db.execute(
            select(News).where(News.asset_id == asset_id, News.published_at >= cutoff)
        )
        .scalars()
        .all()
    )
    if not rows:
        return 0.0
    return sum(n.sentiment for n in rows) / len(rows)


def _price_return_6h(df: pd.DataFrame) -> float:
    if df.empty or len(df) < 2:
        return 0.0
    cutoff = datetime.utcnow() - timedelta(hours=6)
    before = df[df.index <= cutoff]
    if before.empty:
        return float((df["c"].iloc[-1] - df["c"].iloc[0]) / df["c"].iloc[0])
    return float((df["c"].iloc[-1] - before["c"].iloc[-1]) / before["c"].iloc[-1])


@router.get("")
def asset_intel(asset: str = Query("EURUSD"), db: Session = Depends(get_db)) -> dict:
    a = db.execute(select(Asset).where(Asset.symbol == asset)).scalar_one_or_none()
    if a is None:
        raise HTTPException(404, "Asset not found")

    df = _load_ohlcv_df(db, a.id)
    ev = _next_event_for(db, asset)
    minutes_to_event = int((ev.event_time - datetime.utcnow()).total_seconds() / 60) if ev else None
    anticipation = anticipation_pressure(ev) if ev else 0

    s = stress.detect(df, next_event_minutes=minutes_to_event)
    zones = liquidity.detect(df)
    sm = smart_money.estimate(df)
    sent6 = _sentiment_last_6h(db, a.id)
    ret6 = _price_return_6h(df)
    contra = contradiction.detect(sent6, ret6)
    cd = countdown.summarize(ev.event_time if ev else None, anticipation, s.compression_ratio)

    explanation_bits = []
    if s.level != "LOW":
        explanation_bits.append(s.reason)
    if contra.flagged:
        explanation_bits.append(contra.note)
    if sm.flow != "BALANCED":
        explanation_bits.append(f"smart money {sm.flow.lower()}")
    if cd.fake_move_risk != "LOW":
        explanation_bits.append(cd.note)
    explanation = "; ".join(explanation_bits) or "calm, no unusual tension"

    return {
        "asset": asset,
        "ts": datetime.utcnow().isoformat() + "Z",
        "market_state": s.level,
        "stress": {
            "score": s.score,
            "level": s.level,
            "compression_ratio": round(s.compression_ratio, 3),
            "range_ratio": round(s.range_ratio, 3),
            "reason": s.reason,
        },
        "liquidity_zones": [
            {"level": round(z.level, 5), "side": z.side, "touches": z.touches, "distance_pct": z.distance_pct}
            for z in zones
        ],
        "smart_money_flow": {
            "flow": sm.flow,
            "score": sm.score,
            "trap_probability": sm.trap_probability,
            "notes": sm.notes,
        },
        "contradiction": {
            "flagged": contra.flagged,
            "direction": contra.direction,
            "news_bias": round(contra.news_bias, 3),
            "price_return": round(contra.price_return, 5),
            "note": contra.note,
        },
        "pre_news": {
            "minutes_to_event": cd.minutes_to_event,
            "anticipation": cd.anticipation,
            "pressure": cd.pressure,
            "fake_move_risk": cd.fake_move_risk,
            "note": cd.note,
            "event_kind": ev.kind if ev else None,
        },
        "explanation": explanation,
    }


@router.get("/replay")
def replay_similar(
    asset: str = Query("EURUSD"),
    news_id: int | None = Query(None),
    limit: int = Query(5, le=20),
    db: Session = Depends(get_db),
) -> dict:
    a = db.execute(select(Asset).where(Asset.symbol == asset)).scalar_one_or_none()
    if a is None:
        raise HTTPException(404, "Asset not found")
    if news_id is None:
        target = (
            db.execute(
                select(News).where(News.asset_id == a.id).order_by(News.published_at.desc()).limit(1)
            )
            .scalar_one_or_none()
        )
    else:
        target = db.get(News, news_id)
    if target is None:
        return {"target": None, "outcomes": []}

    outcomes = replay.replay_for(db, target, a.id, limit=limit)
    return {
        "target": {
            "id": target.id,
            "title": target.title,
            "published_at": target.published_at.isoformat() + "Z",
            "sentiment": target.sentiment,
            "impact": target.impact,
        },
        "outcomes": [
            {
                "news_id": o.news_id,
                "title": o.title,
                "published_at": o.published_at,
                "similarity": o.similarity,
                "ret_15m": o.ret_15m,
                "ret_1h": o.ret_1h,
                "ret_4h": o.ret_4h,
            }
            for o in outcomes
        ],
    }
