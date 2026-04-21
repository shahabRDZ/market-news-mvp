"""Today's Brief: 3-sentence plain-English market summary.

Reads the same state the dashboard does and composes a brief that a newcomer
can parse in 5 seconds. No jargon.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Asset, EconomicEvent, News, Signal
from ..services.events_fetcher import anticipation_pressure

router = APIRouter()


def _mood_sentence(db: Session) -> str:
    assets = db.execute(select(Asset)).scalars().all()
    ups = downs = 0
    for a in assets:
        last = db.execute(
            select(Signal).where(Signal.asset_id == a.id).order_by(Signal.ts.desc()).limit(1)
        ).scalar_one_or_none()
        if not last:
            continue
        if last.direction == "UP":
            ups += 1
        elif last.direction == "DOWN":
            downs += 1
    if ups > downs:
        return "Good morning. Markets are leaning up across the board."
    if downs > ups:
        return "Heads up. Markets are under pressure right now."
    return "Mixed open. No clear direction yet."


def _driver_sentence(db: Session) -> str:
    cutoff = datetime.utcnow() - timedelta(hours=6)
    news = db.execute(
        select(News).where(News.published_at >= cutoff, News.impact == "HIGH").order_by(News.published_at.desc()).limit(1)
    ).scalar_one_or_none()
    if news:
        tone = "positive" if news.sentiment > 0.15 else "negative" if news.sentiment < -0.15 else "neutral"
        return f"The big driver: \"{news.title[:120]}\" ({tone} tone, from {news.source})."
    any_news = db.execute(
        select(News).where(News.published_at >= cutoff).order_by(News.published_at.desc()).limit(1)
    ).scalar_one_or_none()
    if any_news:
        return f"No high-impact news yet; most recent was \"{any_news.title[:110]}\"."
    return "Quiet newswires so far."


def _event_sentence(db: Session) -> str:
    now = datetime.utcnow()
    ev = db.execute(
        select(EconomicEvent).where(
            EconomicEvent.event_time >= now,
            EconomicEvent.importance >= 2,
            EconomicEvent.event_time <= now + timedelta(hours=24),
        ).order_by(EconomicEvent.event_time.asc()).limit(1)
    ).scalar_one_or_none()
    if not ev:
        return "No major economic events in the next 24 hours."
    minutes = int((ev.event_time - now).total_seconds() / 60)
    if minutes < 90:
        return f"Watch out: {ev.kind} ({ev.country}) in {minutes}m. This usually moves the market."
    hours = minutes // 60
    return f"On the calendar: {ev.kind} ({ev.country}) in about {hours}h."


@router.get("/brief")
def todays_brief(db: Session = Depends(get_db)) -> dict:
    sentences = [_mood_sentence(db), _driver_sentence(db), _event_sentence(db)]
    return {"sentences": sentences, "text": " ".join(sentences)}
