from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import EconomicEvent

EVENTS_PATH = Path(__file__).resolve().parent.parent / "data" / "mock_events.json"


def seed_events(db: Session) -> int:
    existing = db.execute(select(EconomicEvent)).scalars().all()
    if existing:
        return 0
    raw = json.loads(EVENTS_PATH.read_text())
    now = datetime.utcnow()
    count = 0
    for item in raw:
        ev = EconomicEvent(
            kind=item["kind"],
            country=item["country"],
            importance=int(item.get("importance", 1)),
            event_time=now + timedelta(hours=float(item.get("offset_hours", 0))),
            forecast=item.get("forecast"),
            previous=item.get("previous"),
            affected_assets=item.get("affected", []),
        )
        db.add(ev)
        count += 1
    db.commit()
    return count


def anticipation_pressure(event: EconomicEvent, now: datetime | None = None) -> int:
    """Scale 0-100 based on importance and time-to-event.
    Peaks as dt -> 0 for Tier-1 events.
    """
    now = now or datetime.utcnow()
    dt_hours = (event.event_time - now).total_seconds() / 3600.0
    if dt_hours <= 0 or dt_hours > 48:
        return 0
    decay = max(0.0, 1.0 - (dt_hours / 48.0))
    base = {1: 20, 2: 45, 3: 85}.get(event.importance, 20)
    return int(min(100, base * (0.4 + 0.6 * decay)))
