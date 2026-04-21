from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from ..config import settings
from ..db import SessionLocal
from ..models import Asset, News, Signal
from ..services import indicators as ind
from ..services import market_fetcher, news_fetcher, signal_engine
from ..services.broadcaster import broadcaster
from ..services.features import bets as bets_svc

log = logging.getLogger("scheduler")


def _recompute_signal_sync(asset_symbol: str) -> dict | None:
    with SessionLocal() as db:
        asset = db.execute(select(Asset).where(Asset.symbol == asset_symbol)).scalar_one_or_none()
        if asset is None:
            return None
        closes = market_fetcher.load_closes(db, asset_symbol)
        if closes.empty:
            technical_score_val = 0.0
            trend = "flat"
            indi = {"rsi": 50.0, "ma20": 0.0, "ma50": 0.0, "trend": "flat"}
        else:
            indi = ind.compute_all(closes)
            technical_score_val = signal_engine.technical_score(
                indi["rsi"], indi["ma20"], indi["ma50"]
            )
            trend = indi["trend"]

        cutoff = datetime.utcnow() - timedelta(hours=6)
        recent_news = db.execute(
            select(News).where(News.asset_id == asset.id, News.published_at >= cutoff)
        ).scalars().all()
        if recent_news:
            sentiment_val = sum(n.sentiment for n in recent_news) / len(recent_news)
        else:
            sentiment_val = 0.0
        impact_counts: dict[str, int] = {}
        for n in recent_news:
            impact_counts[n.impact] = impact_counts.get(n.impact, 0) + 1
        impact_strength = signal_engine.impact_from_news(impact_counts)

        probs = signal_engine.blend(sentiment_val, technical_score_val)
        direction = signal_engine.direction_of(probs)
        reason = signal_engine.reason_for(sentiment_val, technical_score_val, trend)

        sig = Signal(
            asset_id=asset.id,
            direction=direction,
            prob_up=probs["up"],
            prob_down=probs["down"],
            prob_neutral=probs["neutral"],
            sentiment_score=round(sentiment_val, 4),
            technical_score=round(technical_score_val, 4),
            impact_strength=impact_strength,
            reason=reason,
            details={"indicators": indi, "news_considered": len(recent_news)},
        )
        db.add(sig)
        db.commit()
        db.refresh(sig)

        return {
            "asset": asset_symbol,
            "ts": sig.ts.isoformat() + "Z",
            "probabilities": probs,
            "direction": direction,
            "sentiment_score": sig.sentiment_score,
            "technical_score": sig.technical_score,
            "impact_strength": impact_strength,
            "reason": reason,
        }


async def job_fetch_news(asset_symbol: str = "EURUSD") -> None:
    log.info("Fetching news for %s", asset_symbol)
    loop = asyncio.get_running_loop()

    def _work():
        with SessionLocal() as db:
            return news_fetcher.fetch_and_store(db, asset_symbol)

    inserted = await loop.run_in_executor(None, _work)
    if inserted:
        for n in inserted:
            await broadcaster.publish(
                {
                    "type": "news.new",
                    "asset": asset_symbol,
                    "payload": {
                        "id": n.id,
                        "source": n.source,
                        "title": n.title,
                        "url": n.url,
                        "published_at": n.published_at.isoformat() + "Z",
                        "sentiment": n.sentiment,
                        "impact": n.impact,
                    },
                }
            )
        for sym in ("EURUSD", "BTCUSD", "XAUUSD"):
            payload = await loop.run_in_executor(None, _recompute_signal_sync, sym)
            if payload:
                await broadcaster.publish({"type": "signal.updated", "asset": sym, "payload": payload})


async def job_fetch_market(asset_symbol: str = "EURUSD") -> None:
    log.info("Fetching market for %s", asset_symbol)
    loop = asyncio.get_running_loop()

    def _work():
        with SessionLocal() as db:
            df = market_fetcher.fetch_ohlcv(asset_symbol)
            return market_fetcher.store_ohlcv(db, asset_symbol, df)

    try:
        added = await loop.run_in_executor(None, _work)
    except Exception as exc:
        log.warning("market fetch failed: %s", exc)
        added = 0
    if added:
        payload = await loop.run_in_executor(None, _recompute_signal_sync, asset_symbol)
        if payload:
            await broadcaster.publish({"type": "signal.updated", "asset": asset_symbol, "payload": payload})


TRACKED_ASSETS = ["EURUSD", "BTCUSD", "XAUUSD"]


async def job_fetch_news_all() -> None:
    # News is global; we fetch once and tag EURUSD for now. Other assets reuse the pool.
    await job_fetch_news("EURUSD")


async def job_fetch_market_all() -> None:
    for sym in TRACKED_ASSETS:
        try:
            await job_fetch_market(sym)
        except Exception as exc:
            log.warning("market job failed for %s: %s", sym, exc)


async def job_resolve_bets() -> None:
    loop = asyncio.get_running_loop()

    def _work() -> int:
        with SessionLocal() as db:
            return bets_svc.resolve_due(db)

    try:
        resolved = await loop.run_in_executor(None, _work)
        if resolved:
            log.info("resolved %d paper bets", resolved)
    except Exception as exc:
        log.warning("bet resolution failed: %s", exc)


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(job_fetch_news_all, "interval", seconds=settings.POLL_NEWS_SECONDS, id="news")
    scheduler.add_job(job_fetch_market_all, "interval", seconds=settings.POLL_MARKET_SECONDS, id="market")
    scheduler.add_job(job_resolve_bets, "interval", seconds=120, id="bets")
    return scheduler
