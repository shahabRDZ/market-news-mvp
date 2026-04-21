"""MVP signal formula kept pure for reuse and swapping."""
from __future__ import annotations


def technical_score(rsi: float, ma_short: float, ma_long: float) -> float:
    rsi_component = (rsi - 50.0) / 50.0
    cross_component = 1.0 if ma_short > ma_long else (-1.0 if ma_short < ma_long else 0.0)
    return max(-1.0, min(1.0, 0.6 * rsi_component + 0.4 * cross_component))


def blend(sentiment: float, technical: float) -> dict:
    raw = 0.5 * sentiment + 0.5 * technical
    up = max(0.0, raw)
    down = max(0.0, -raw)
    neutral = max(0.05, 0.4 - abs(raw))
    total = up + down + neutral
    return {"up": up / total, "down": down / total, "neutral": neutral / total}
