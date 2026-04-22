from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import api_key_user
from ..db import get_db
from ..models import Asset, News, Signal, User
from ..schemas import NewsItem, NewsList, SignalResponse, Probabilities
from ..services.plans import get_plan
from ..services.rate_limit import rate_limiter

router = APIRouter(prefix="/v1", tags=["v1"])


def _check_rate(response: Response, user: User) -> None:
    plan = get_plan(user.plan)
    allowed, remaining, reset_in = rate_limiter.check(
        key=f"v1:user:{user.id}",
        limit=plan.api_calls_per_day,
        window_seconds=86400,
    )
    response.headers["X-RateLimit-Limit"] = str(plan.api_calls_per_day)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_in)
    if not allowed:
        raise HTTPException(429, f"Rate limit exceeded on plan {plan.name}. Upgrade for more requests.")


@router.get("/assets")
def list_assets(
    response: Response,
    user: User = Depends(api_key_user),
    db: Session = Depends(get_db),
) -> dict:
    _check_rate(response, user)
    rows = db.execute(select(Asset)).scalars().all()
    return {"assets": [{"symbol": r.symbol, "name": r.display_name} for r in rows]}


@router.get("/news", response_model=NewsList)
def get_news(
    response: Response,
    asset: str = Query("EURUSD"),
    limit: int = Query(20, le=100),
    user: User = Depends(api_key_user),
    db: Session = Depends(get_db),
) -> NewsList:
    _check_rate(response, user)
    a = db.execute(select(Asset).where(Asset.symbol == asset)).scalar_one_or_none()
    if a is None:
        return NewsList(items=[])
    rows = db.execute(
        select(News).where(News.asset_id == a.id).order_by(News.published_at.desc()).limit(limit)
    ).scalars().all()
    return NewsList(
        items=[
            NewsItem(
                id=r.id,
                source=r.source,
                title=r.title,
                url=r.url,
                published_at=r.published_at,
                sentiment=r.sentiment,
                impact=r.impact,
            )
            for r in rows
        ]
    )


@router.get("/signal", response_model=SignalResponse)
def get_signal(
    response: Response,
    asset: str = Query("EURUSD"),
    user: User = Depends(api_key_user),
    db: Session = Depends(get_db),
) -> SignalResponse:
    _check_rate(response, user)
    a = db.execute(select(Asset).where(Asset.symbol == asset)).scalar_one_or_none()
    if a is None:
        raise HTTPException(404, "Asset not found")
    row = db.execute(select(Signal).where(Signal.asset_id == a.id).order_by(Signal.ts.desc()).limit(1)).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "No signal yet, try again shortly")
    return SignalResponse(
        asset=asset,
        ts=row.ts,
        probabilities=Probabilities(up=row.prob_up, down=row.prob_down, neutral=row.prob_neutral),
        direction=row.direction,
        sentiment_score=row.sentiment_score,
        technical_score=row.technical_score,
        impact_strength=row.impact_strength,
        reason=row.reason,
    )


def _csv_response(headers: list[str], rows: list[list]) -> PlainTextResponse:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    w.writerows(rows)
    return PlainTextResponse(buf.getvalue(), media_type="text/csv; charset=utf-8")


@router.get("/news.csv")
def get_news_csv(
    response: Response,
    asset: str = Query("EURUSD"),
    limit: int = Query(100, le=1000),
    user: User = Depends(api_key_user),
    db: Session = Depends(get_db),
) -> PlainTextResponse:
    _check_rate(response, user)
    a = db.execute(select(Asset).where(Asset.symbol == asset)).scalar_one_or_none()
    if a is None:
        return _csv_response(["id", "source", "title", "url", "published_at", "sentiment", "impact"], [])
    rows = db.execute(
        select(News).where(News.asset_id == a.id).order_by(News.published_at.desc()).limit(limit)
    ).scalars().all()
    body = [
        [r.id, r.source, r.title, r.url, r.published_at.isoformat() + "Z", r.sentiment, r.impact]
        for r in rows
    ]
    out = _csv_response(
        ["id", "source", "title", "url", "published_at", "sentiment", "impact"], body
    )
    out.headers["Content-Disposition"] = f'attachment; filename="news_{asset}.csv"'
    for h in ("X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"):
        if h in response.headers:
            out.headers[h] = response.headers[h]
    return out


@router.get("/signals.csv")
def get_signals_csv(
    response: Response,
    asset: str = Query("EURUSD"),
    limit: int = Query(500, le=5000),
    user: User = Depends(api_key_user),
    db: Session = Depends(get_db),
) -> PlainTextResponse:
    _check_rate(response, user)
    a = db.execute(select(Asset).where(Asset.symbol == asset)).scalar_one_or_none()
    headers = [
        "ts", "direction", "prob_up", "prob_down", "prob_neutral",
        "sentiment_score", "technical_score", "impact_strength", "reason",
    ]
    if a is None:
        return _csv_response(headers, [])
    rows = db.execute(
        select(Signal).where(Signal.asset_id == a.id).order_by(Signal.ts.desc()).limit(limit)
    ).scalars().all()
    body = [
        [
            r.ts.isoformat() + "Z", r.direction,
            r.prob_up, r.prob_down, r.prob_neutral,
            r.sentiment_score, r.technical_score, r.impact_strength, r.reason,
        ]
        for r in rows
    ]
    out = _csv_response(headers, body)
    out.headers["Content-Disposition"] = f'attachment; filename="signals_{asset}.csv"'
    for h in ("X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"):
        if h in response.headers:
            out.headers[h] = response.headers[h]
    return out
