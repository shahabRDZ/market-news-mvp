"""Smart money flow estimator (rule-based).

Signals:
- Volume z-score: unusual participation.
- Body-to-range ratio: small body with long wick on high volume suggests absorption.
- Close location: closing near the high on up bars (near low on down bars) with
  above-average volume signals directional flow.
- Divergence: up-bar volume cluster without price progress implies absorption by sellers.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class SmartMoneyResult:
    flow: str   # "INFLOW" | "OUTFLOW" | "BALANCED"
    score: int  # -100..+100
    trap_probability: int  # 0..100
    notes: list[str]


def _zscore(series: pd.Series, window: int = 50) -> float:
    if len(series) < window:
        return 0.0
    tail = series.tail(window)
    std = tail.std() or 1e-9
    return float((series.iloc[-1] - tail.mean()) / std)


def estimate(df: pd.DataFrame) -> SmartMoneyResult:
    if df is None or df.empty or len(df) < 60:
        return SmartMoneyResult("BALANCED", 0, 0, ["insufficient data"])

    last = df.iloc[-1]
    body = abs(last["c"] - last["o"])
    rng = max(last["h"] - last["l"], 1e-9)
    body_ratio = float(body / rng)
    upper_wick = float(last["h"] - max(last["c"], last["o"])) / rng
    lower_wick = float(min(last["c"], last["o"]) - last["l"]) / rng
    direction = 1 if last["c"] > last["o"] else (-1 if last["c"] < last["o"] else 0)

    vol_z = _zscore(df["v"], 50)
    close_pos = float((last["c"] - last["l"]) / rng)

    score = 0
    notes: list[str] = []

    if vol_z > 1.5:
        notes.append(f"volume surge {vol_z:.1f}σ")
        score += int(20 * direction)
        if direction > 0 and close_pos > 0.7:
            score += 25
            notes.append("bullish close at highs")
        elif direction < 0 and close_pos < 0.3:
            score -= 25
            notes.append("bearish close at lows")

    # Wick absorption: big wick opposite direction with high volume implies absorption.
    trap = 0
    if upper_wick > 0.5 and vol_z > 1.0 and direction >= 0:
        trap = 60
        notes.append("upper wick absorption on volume")
        score -= 15
    if lower_wick > 0.5 and vol_z > 1.0 and direction <= 0:
        trap = max(trap, 60)
        notes.append("lower wick absorption on volume")
        score += 15

    # Divergence: price flat/down while volume high -> likely distribution.
    body_zero = body_ratio < 0.2
    if body_zero and vol_z > 1.0:
        notes.append("high volume, small body (absorption)")
        score = int(score * 0.5)
        trap = max(trap, 40)

    score = max(-100, min(100, score))
    if score > 20:
        flow = "INFLOW"
    elif score < -20:
        flow = "OUTFLOW"
    else:
        flow = "BALANCED"

    if not notes:
        notes.append("no unusual participation")

    return SmartMoneyResult(flow=flow, score=score, trap_probability=trap, notes=notes)
