from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import EconomicEvent
from ..schemas import EconomicEventOut, EventsResponse
from ..services.events_fetcher import anticipation_pressure

router = APIRouter()


@router.get("/events", response_model=EventsResponse)
def list_events(
    hours: int = Query(48, le=168),
    importance: int = Query(1, ge=1, le=3),
    db: Session = Depends(get_db),
) -> EventsResponse:
    now = datetime.utcnow()
    horizon = now + timedelta(hours=hours)
    rows = db.execute(
        select(EconomicEvent)
        .where(
            EconomicEvent.event_time >= now - timedelta(hours=1),
            EconomicEvent.event_time <= horizon,
            EconomicEvent.importance >= importance,
        )
        .order_by(EconomicEvent.event_time.asc())
    ).scalars().all()
    return EventsResponse(
        items=[
            EconomicEventOut(
                id=r.id,
                kind=r.kind,
                country=r.country,
                importance=r.importance,
                event_time=r.event_time,
                forecast=r.forecast,
                previous=r.previous,
                actual=r.actual,
                affected_assets=r.affected_assets or [],
                anticipation=anticipation_pressure(r, now),
            )
            for r in rows
        ]
    )
