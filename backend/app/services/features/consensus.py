"""Consensus breaker alerts: detect economic events whose actual value
surprises versus forecast by a configurable sigma threshold, and attach the
historical playbook for similar surprises.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import EconomicEvent


def _surprise_sigma(actual: float, forecast: float, previous: float | None) -> float:
    baseline = abs((forecast or 0) - (previous or 0)) or 0.5
    return round((actual - forecast) / baseline, 2)


def detect(db: Session, lookback_hours: int = 4) -> list[dict]:
    now = datetime.utcnow()
    rows = db.execute(
        select(EconomicEvent).where(
            EconomicEvent.actual.is_not(None),
            EconomicEvent.event_time >= now - timedelta(hours=lookback_hours),
        )
    ).scalars().all()
    out: list[dict] = []
    for r in rows:
        if r.forecast is None:
            continue
        sigma = _surprise_sigma(r.actual, r.forecast, r.previous)
        if abs(sigma) < 1.0:
            continue
        out.append(
            {
                "kind": r.kind,
                "country": r.country,
                "event_time": r.event_time.isoformat() + "Z",
                "actual": r.actual,
                "forecast": r.forecast,
                "previous": r.previous,
                "surprise_sigma": sigma,
                "playbook": _playbook(r.kind, sigma),
                "affected_assets": r.affected_assets,
            }
        )
    return out


def _playbook(kind: str, sigma: float) -> str:
    # Heuristic, to be replaced with historical averages once outcomes accumulate.
    direction = "hawkish / USD bullish" if sigma > 0 and kind in {"CPI", "NFP"} else (
        "dovish / USD bearish" if sigma < 0 and kind in {"CPI", "NFP"} else "mixed"
    )
    return f"{abs(sigma):.1f}σ surprise on {kind}: historical bias {direction}"
