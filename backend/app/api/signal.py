from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Asset, Signal
from ..schemas import Probabilities, SignalResponse

router = APIRouter()


@router.get("/signal", response_model=SignalResponse)
def get_signal(asset: str = Query("EURUSD"), db: Session = Depends(get_db)) -> SignalResponse:
    a = db.execute(select(Asset).where(Asset.symbol == asset)).scalar_one_or_none()
    if a is None:
        return _empty(asset)
    row = db.execute(
        select(Signal).where(Signal.asset_id == a.id).order_by(Signal.ts.desc()).limit(1)
    ).scalar_one_or_none()
    if row is None:
        return _empty(asset)
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


def _empty(asset: str) -> SignalResponse:
    return SignalResponse(
        asset=asset,
        ts=datetime.utcnow(),
        probabilities=Probabilities(up=0.33, down=0.33, neutral=0.34),
        direction="NEUTRAL",
        sentiment_score=0.0,
        technical_score=0.0,
        impact_strength="LOW",
        reason="Warming up, no data yet",
    )
