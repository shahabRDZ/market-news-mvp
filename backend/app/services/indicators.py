from __future__ import annotations

import pandas as pd


def rsi(series: pd.Series, period: int = 14) -> float:
    if len(series) < period + 1:
        return 50.0
    delta = series.diff().dropna()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, 1e-9)
    value = 100 - (100 / (1 + rs))
    last = value.iloc[-1]
    if pd.isna(last):
        return 50.0
    return float(last)


def moving_average(series: pd.Series, period: int) -> float:
    if len(series) < period:
        return float(series.mean()) if len(series) else 0.0
    return float(series.rolling(period).mean().iloc[-1])


def trend_direction(ma_short: float, ma_long: float, tolerance: float = 1e-5) -> str:
    if ma_short > ma_long * (1 + tolerance):
        return "up"
    if ma_short < ma_long * (1 - tolerance):
        return "down"
    return "flat"


def compute_all(closes: pd.Series) -> dict:
    ma20 = moving_average(closes, 20)
    ma50 = moving_average(closes, 50)
    return {
        "rsi": rsi(closes, 14),
        "ma20": ma20,
        "ma50": ma50,
        "trend": trend_direction(ma20, ma50),
    }
