"""Pre-news volatility countdown.

Bundles: anticipation pressure (already computed per event), live ATR-compression
ratio, and distance-to-event to produce a single "volatility pressure meter"
and a fake-move risk flag.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CountdownResult:
    minutes_to_event: int
    anticipation: int
    pressure: int
    fake_move_risk: str
    note: str


def summarize(
    event_time: datetime | None,
    anticipation: int,
    compression_ratio: float,
) -> CountdownResult:
    if event_time is None:
        return CountdownResult(0, 0, 0, "LOW", "no imminent event")
    minutes = max(0, int((event_time - datetime.utcnow()).total_seconds() / 60))
    proximity = max(0, min(100, 100 - int(minutes * 100 / (60 * 4))))  # full within 4h
    comp_bonus = int(max(0, (1.0 - compression_ratio) * 50))
    pressure = min(100, int(0.5 * anticipation + 0.3 * proximity + 0.2 * comp_bonus))
    if pressure >= 70 and compression_ratio < 0.7:
        fake_risk = "HIGH"
        note = "Tight range into a tier-1 event; first move may be a fakeout"
    elif pressure >= 50:
        fake_risk = "MED"
        note = "Meaningful pressure building ahead of the event"
    else:
        fake_risk = "LOW"
        note = "Calm ahead of event"
    return CountdownResult(minutes, anticipation, pressure, fake_risk, note)
