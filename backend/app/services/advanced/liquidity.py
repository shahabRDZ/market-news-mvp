"""Liquidity-zone detector.

Rule: swing highs/lows over a rolling window are proxies for resting liquidity
(stops above swing highs, stops below swing lows). We cluster levels that
repeat within a tolerance and rank by touch count as proxy for stop density.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class LiquidityZone:
    level: float
    side: str  # "above" or "below" (relative to recent price)
    touches: int
    distance_pct: float


def _swing_points(df: pd.DataFrame, left: int = 3, right: int = 3) -> tuple[list[float], list[float]]:
    highs: list[float] = []
    lows: list[float] = []
    h = df["h"].values
    l = df["l"].values
    for i in range(left, len(df) - right):
        window_h = h[i - left : i + right + 1]
        window_l = l[i - left : i + right + 1]
        if h[i] == window_h.max():
            highs.append(float(h[i]))
        if l[i] == window_l.min():
            lows.append(float(l[i]))
    return highs, lows


def _cluster(levels: list[float], tolerance_pct: float) -> list[tuple[float, int]]:
    if not levels:
        return []
    sorted_levels = sorted(levels)
    clusters: list[list[float]] = [[sorted_levels[0]]]
    for v in sorted_levels[1:]:
        anchor = clusters[-1][0]
        if abs(v - anchor) / max(abs(anchor), 1e-9) < tolerance_pct:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    return [(sum(c) / len(c), len(c)) for c in clusters]


def detect(df: pd.DataFrame, tolerance_pct: float = 0.0015, top_n: int = 5) -> list[LiquidityZone]:
    if df is None or df.empty or len(df) < 40:
        return []
    highs, lows = _swing_points(df, 3, 3)
    clustered = _cluster(highs + lows, tolerance_pct)
    last_price = float(df["c"].iloc[-1])
    zones: list[LiquidityZone] = []
    for level, touches in clustered:
        if touches < 2:
            continue
        dist_pct = (level - last_price) / last_price * 100.0
        zones.append(
            LiquidityZone(
                level=level,
                side="above" if level > last_price else "below",
                touches=touches,
                distance_pct=round(dist_pct, 3),
            )
        )
    zones.sort(key=lambda z: (-z.touches, abs(z.distance_pct)))
    return zones[:top_n]
