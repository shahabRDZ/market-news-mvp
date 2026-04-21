from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response
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
