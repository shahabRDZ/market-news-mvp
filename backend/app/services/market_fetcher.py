from __future__ import annotations

from datetime import datetime
from typing import Iterable

import pandas as pd
import yfinance as yf
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Asset, Candle

SYMBOL_MAP = {
    "EURUSD": "EURUSD=X",
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
    "XAUUSD": "GC=F",
}


def _to_naive(ts) -> datetime:
    if hasattr(ts, "to_pydatetime"):
        ts = ts.to_pydatetime()
    if ts.tzinfo is not None:
        ts = ts.replace(tzinfo=None)
    return ts


def fetch_ohlcv(asset_symbol: str, interval: str = "15m", period: str = "5d") -> pd.DataFrame:
    ticker = SYMBOL_MAP.get(asset_symbol)
    if not ticker:
        return pd.DataFrame()
    t = yf.Ticker(ticker)
    df = t.history(period=period, interval=interval, auto_adjust=False)
    if df.empty:
        return df
    df = df.rename(columns={"Open": "o", "High": "h", "Low": "l", "Close": "c", "Volume": "v"})
    return df[["o", "h", "l", "c", "v"]]


def store_ohlcv(db: Session, asset_symbol: str, df: pd.DataFrame, timeframe: str = "15m") -> int:
    asset = db.execute(select(Asset).where(Asset.symbol == asset_symbol)).scalar_one_or_none()
    if asset is None or df.empty:
        return 0
    existing = {
        ts
        for ts in db.execute(
            select(Candle.ts).where(Candle.asset_id == asset.id, Candle.timeframe == timeframe)
        ).scalars()
    }
    added = 0
    for idx, row in df.iterrows():
        ts = _to_naive(idx)
        if ts in existing:
            continue
        c = Candle(
            asset_id=asset.id,
            timeframe=timeframe,
            ts=ts,
            o=float(row["o"]),
            h=float(row["h"]),
            l=float(row["l"]),
            c=float(row["c"]),
            v=float(row["v"] or 0.0),
        )
        db.add(c)
        added += 1
    if added:
        db.commit()
    return added


def load_closes(db: Session, asset_symbol: str, timeframe: str = "15m", limit: int = 200) -> pd.Series:
    asset = db.execute(select(Asset).where(Asset.symbol == asset_symbol)).scalar_one_or_none()
    if asset is None:
        return pd.Series(dtype=float)
    rows = db.execute(
        select(Candle).where(Candle.asset_id == asset.id, Candle.timeframe == timeframe).order_by(Candle.ts.desc()).limit(limit)
    ).scalars().all()
    rows = sorted(rows, key=lambda r: r.ts)
    if not rows:
        return pd.Series(dtype=float)
    return pd.Series([r.c for r in rows], index=[r.ts for r in rows])
