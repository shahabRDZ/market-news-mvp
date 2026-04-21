"""Pre-news stress / volatility compression detector.

Rule: compare short-window realized volatility vs long-window baseline.
If short vol < 0.6 * long vol while price drifts into a range, the market
is compressing. Combined with proximity to a high-impact event, emit HIGH.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd


@dataclass
class StressResult:
    score: int
    level: str
    compression_ratio: float
    range_ratio: float
    minutes_to_event: int | None
    reason: str


def _true_range(df: pd.DataFrame) -> pd.Series:
    prev_c = df["c"].shift(1)
    tr = pd.concat(
        [
            (df["h"] - df["l"]).abs(),
            (df["h"] - prev_c).abs(),
            (df["l"] - prev_c).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr


def detect(df: pd.DataFrame, next_event_minutes: int | None = None) -> StressResult:
    if df is None or df.empty or len(df) < 50:
        return StressResult(0, "LOW", 1.0, 1.0, next_event_minutes, "insufficient data")

    tr = _true_range(df)
    atr_short = tr.rolling(14).mean().iloc[-1]
    atr_long = tr.rolling(50).mean().iloc[-1]
    if atr_long and atr_long > 0:
        compression = float(atr_short / atr_long)
    else:
        compression = 1.0

    recent = df.tail(30)
    rng = (recent["h"].max() - recent["l"].min())
    baseline_rng = (df["h"].tail(120).max() - df["l"].tail(120).min()) or 1e-9
    range_ratio = float(rng / baseline_rng)

    # Score: lower compression + tighter range + closer to event = higher stress
    score = 0
    if compression < 0.8:
        score += 25
    if compression < 0.6:
        score += 25
    if range_ratio < 0.5:
        score += 20
    if next_event_minutes is not None and next_event_minutes <= 60:
        score += 30
    elif next_event_minutes is not None and next_event_minutes <= 240:
        score += 15
    score = min(100, score)

    if score >= 70:
        level = "HIGH"
    elif score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    reason_bits = []
    if compression < 0.8:
        reason_bits.append(f"ATR compressed to {compression:.2f}x baseline")
    if range_ratio < 0.5:
        reason_bits.append("price range tightening")
    if next_event_minutes is not None and next_event_minutes <= 60:
        reason_bits.append(f"event in {next_event_minutes}m")
    reason = "; ".join(reason_bits) or "stable regime"

    return StressResult(score, level, compression, range_ratio, next_event_minutes, reason)
