"""Asset personality card.

Static + dynamic profile per asset. Daily vol is computed from stored candles;
keyword sensitivity is a curated map until labeled reactions accumulate.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import Asset, Candle

STATIC = {
    "EURUSD": {
        "class": "FX Major",
        "most_reactive_to": ["US CPI", "FOMC", "ECB", "NFP"],
        "least_reactive_to": ["China PMI", "crypto headlines"],
        "active_hours_utc": "07:00-16:00",
        "typical_daily_pip_range": "60-90",
    },
    "BTCUSD": {
        "class": "Crypto",
        "most_reactive_to": ["ETF flows", "SEC actions", "whale liquidations"],
        "least_reactive_to": ["scheduled macro releases (second-order)"],
        "active_hours_utc": "00:00-23:59",
        "typical_daily_pct_range": "2-5%",
    },
    "XAUUSD": {
        "class": "Metal",
        "most_reactive_to": ["real yields", "USD", "geopolitical risk"],
        "least_reactive_to": ["single earnings reports"],
        "active_hours_utc": "07:00-22:00",
        "typical_daily_pct_range": "0.6-1.5%",
    },
}


def profile(db: Session, symbol: str) -> dict:
    static = STATIC.get(symbol, {"class": "unknown"})
    a = db.execute(select(Asset).where(Asset.symbol == symbol)).scalar_one_or_none()
    dyn = {}
    if a is not None:
        rows = db.execute(
            select(Candle)
            .where(Candle.asset_id == a.id, Candle.timeframe == "15m", Candle.ts >= datetime.utcnow() - timedelta(days=7))
            .order_by(Candle.ts.asc())
        ).scalars().all()
        if rows:
            s = pd.Series([r.c for r in rows])
            daily_ret = s.pct_change().dropna()
            dyn = {
                "recent_daily_vol_pct": round(float(daily_ret.std() * 100 * (96 ** 0.5)), 3),
                "recent_range_pct": round(float((s.max() - s.min()) / s.iloc[0] * 100), 3),
                "samples": int(len(s)),
            }
    return {"symbol": symbol, "static": static, "dynamic": dyn}
