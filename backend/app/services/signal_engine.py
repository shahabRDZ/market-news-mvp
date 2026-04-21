from __future__ import annotations


def technical_score(rsi: float, ma_short: float, ma_long: float) -> float:
    rsi_component = (rsi - 50.0) / 50.0
    cross_component = 1.0 if ma_short > ma_long else (-1.0 if ma_short < ma_long else 0.0)
    raw = 0.6 * rsi_component + 0.4 * cross_component
    return max(-1.0, min(1.0, raw))


def blend(sentiment: float, technical: float) -> dict:
    raw = 0.5 * sentiment + 0.5 * technical
    up = max(0.0, raw)
    down = max(0.0, -raw)
    neutral = max(0.05, 0.4 - abs(raw))
    total = up + down + neutral
    return {
        "up": round(up / total, 4),
        "down": round(down / total, 4),
        "neutral": round(neutral / total, 4),
    }


def direction_of(probs: dict) -> str:
    m = max(probs, key=probs.get)
    return {"up": "UP", "down": "DOWN", "neutral": "NEUTRAL"}[m]


def reason_for(sentiment: float, technical: float, trend: str) -> str:
    if abs(sentiment) > abs(technical):
        tone = "positive" if sentiment > 0 else "negative"
        return f"Driven by {tone} news flow"
    return f"Driven by technical trend ({trend})"


def impact_from_news(impact_counts: dict) -> str:
    if impact_counts.get("HIGH", 0) > 0:
        return "HIGH"
    if impact_counts.get("MED", 0) > 1:
        return "MED"
    return "LOW"
