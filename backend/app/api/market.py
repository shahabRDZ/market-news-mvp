from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Asset, Candle
from ..schemas import Candle as CandleSchema
from ..schemas import Indicators, MarketResponse
from ..services import indicators as ind
from ..services import market_fetcher

router = APIRouter()


@router.get("/market", response_model=MarketResponse)
def get_market(
    asset: str = Query("EURUSD"),
    timeframe: str = Query("15m"),
    limit: int = Query(96, le=500),
    db: Session = Depends(get_db),
) -> MarketResponse:
    a = db.execute(select(Asset).where(Asset.symbol == asset)).scalar_one_or_none()
    if a is None:
        return MarketResponse(asset=asset, timeframe=timeframe, candles=[])
    rows = db.execute(
        select(Candle)
        .where(Candle.asset_id == a.id, Candle.timeframe == timeframe)
        .order_by(Candle.ts.desc())
        .limit(limit)
    ).scalars().all()
    rows = sorted(rows, key=lambda r: r.ts)
    candles = [
        CandleSchema(ts=r.ts, o=r.o, h=r.h, l=r.l, c=r.c, v=r.v) for r in rows
    ]
    closes = market_fetcher.load_closes(db, asset, timeframe, limit=200)
    indicators = None
    if not closes.empty:
        raw = ind.compute_all(closes)
        indicators = Indicators(
            rsi=round(raw["rsi"], 2),
            ma20=round(raw["ma20"], 5),
            ma50=round(raw["ma50"], 5),
            trend=raw["trend"],
        )
    return MarketResponse(asset=asset, timeframe=timeframe, candles=candles, indicators=indicators)
