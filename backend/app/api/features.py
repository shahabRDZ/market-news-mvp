from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, optional_user
from ..db import get_db
from ..models import Asset, News, Pattern, User
from ..services.features import (
    bets,
    boring,
    calibration,
    consensus,
    contagion,
    correlation,
    digest,
    narrative,
    patterns as patterns_svc,
    personality,
    silence,
    sources,
    timemachine,
)

router = APIRouter(prefix="/features", tags=["features"])


# ---------- Time Machine ----------

@router.get("/timemachine")
def time_machine(
    as_of: datetime = Query(..., description="ISO timestamp"),
    db: Session = Depends(get_db),
) -> dict:
    return {
        "as_of": as_of.isoformat() + "Z",
        "signals": timemachine.snapshot_signals(db, as_of),
        "news": timemachine.snapshot_news(db, as_of),
    }


# ---------- Narrative tracking ----------

@router.get("/narratives")
def narratives(db: Session = Depends(get_db)) -> dict:
    return {"items": narrative.detect(db)}


# ---------- Silence ----------

@router.get("/silence")
def silence_state(db: Session = Depends(get_db)) -> dict:
    return silence.detect(db)


# ---------- Consensus breaker ----------

@router.get("/consensus")
def consensus_alerts(db: Session = Depends(get_db)) -> dict:
    return {"items": consensus.detect(db)}


# ---------- Correlation break ----------

@router.get("/correlation")
def correlation_breaks(db: Session = Depends(get_db)) -> dict:
    return {"items": correlation.detect(db)}


# ---------- Did I miss anything ----------

@router.get("/digest")
def digest_since_last_seen(
    u: User = Depends(current_user), db: Session = Depends(get_db)
) -> dict:
    data = digest.build(db, u)
    digest.touch(db, u)
    return data


# ---------- Pattern library ----------

class PatternIn(BaseModel):
    name: str
    rules: dict
    active: bool = True


class PatternOut(BaseModel):
    id: int
    name: str
    rules: dict
    active: bool
    last_matched_at: str | None = None


@router.get("/patterns")
def list_patterns(u: User = Depends(current_user), db: Session = Depends(get_db)) -> list[PatternOut]:
    rows = db.execute(select(Pattern).where(Pattern.user_id == u.id).order_by(Pattern.created_at.desc())).scalars().all()
    return [
        PatternOut(
            id=p.id,
            name=p.name,
            rules=p.rules,
            active=p.active,
            last_matched_at=(p.last_matched_at.isoformat() + "Z") if p.last_matched_at else None,
        )
        for p in rows
    ]


@router.post("/patterns")
def create_pattern(body: PatternIn, u: User = Depends(current_user), db: Session = Depends(get_db)) -> PatternOut:
    cleaned = patterns_svc.validate_rules(body.rules)
    if not cleaned:
        raise HTTPException(400, "No supported rule keys provided")
    p = Pattern(user_id=u.id, name=body.name[:64], rules=cleaned, active=body.active)
    db.add(p)
    db.commit()
    db.refresh(p)
    return PatternOut(id=p.id, name=p.name, rules=p.rules, active=p.active, last_matched_at=None)


@router.delete("/patterns/{pid}")
def delete_pattern(pid: int, u: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    p = db.get(Pattern, pid)
    if p is None or p.user_id != u.id:
        raise HTTPException(404, "pattern not found")
    db.delete(p)
    db.commit()
    return {"ok": True}


@router.get("/patterns/matches")
def pattern_matches(
    mood_label: str = Query("Mixed"),
    u: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    return {"matches": patterns_svc.evaluate(db, u.id, mood_label)}


# ---------- Calibration ----------

@router.get("/calibration")
def calibration_curve(
    horizon: int = Query(60, le=1440),
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
) -> dict:
    return calibration.compute(db, horizon_min=horizon, days=days)


# ---------- Retail vs institutional ----------

@router.get("/sources")
def sentiment_split(hours: int = Query(24, le=168), db: Session = Depends(get_db)) -> dict:
    return sources.split(db, hours=hours)


# ---------- Asset personality ----------

@router.get("/personality/{symbol}")
def personality_card(symbol: str, db: Session = Depends(get_db)) -> dict:
    return personality.profile(db, symbol)


# ---------- Paper bets ----------

class PlaceBetIn(BaseModel):
    asset: str
    direction: str
    horizon_minutes: int = 60


@router.post("/bets")
def place_bet(body: PlaceBetIn, u: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    if body.direction.upper() not in {"UP", "DOWN", "NEUTRAL"}:
        raise HTTPException(400, "direction must be UP, DOWN, or NEUTRAL")
    try:
        bet = bets.place(db, u, body.asset, body.direction, body.horizon_minutes)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {
        "id": bet.id,
        "asset": bet.asset_symbol,
        "direction": bet.direction,
        "horizon_minutes": bet.horizon_minutes,
        "placed_price": bet.placed_price,
        "resolve_at": bet.resolve_at.isoformat() + "Z",
    }


@router.get("/bets")
def bet_stats(u: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return bets.stats(db, u)


# ---------- Contagion ----------

@router.get("/contagion")
def contagion_map(db: Session = Depends(get_db)) -> dict:
    return {"items": contagion.estimate(db)}


# ---------- Boring day ----------

@router.get("/boring")
def boring_state(db: Session = Depends(get_db)) -> dict:
    return boring.assess(db)


# ---------- News markers (for chart scrubbing) ----------

@router.get("/news-markers")
def news_markers(
    asset: str = Query("EURUSD"),
    hours: int = Query(24, le=168),
    db: Session = Depends(get_db),
) -> dict:
    a = db.execute(select(Asset).where(Asset.symbol == asset)).scalar_one_or_none()
    if a is None:
        return {"markers": []}
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    rows = (
        db.execute(
            select(News).where(News.asset_id == a.id, News.published_at >= cutoff).order_by(News.published_at.asc())
        )
        .scalars()
        .all()
    )
    impact_size = {"LOW": 1, "MED": 2, "HIGH": 3}
    return {
        "markers": [
            {
                "id": n.id,
                "ts": int(n.published_at.timestamp()),
                "title": n.title,
                "impact": n.impact,
                "size": impact_size.get(n.impact, 1),
                "sentiment": n.sentiment,
            }
            for n in rows
        ]
    }


# ---------- Soft push hint ----------

@router.get("/push-hint")
def push_hint(
    u: User | None = Depends(optional_user), db: Session = Depends(get_db)
) -> dict:
    """What the UI should show as a tab-badge.
    We return a coarse importance-ranked list of new items since last_seen.
    Anonymous users get the global hint.
    """
    last_seen = u.last_seen_at if u else datetime.utcnow() - timedelta(minutes=10)
    rows = db.execute(
        select(News).where(News.impact == "HIGH", News.published_at >= last_seen)
    ).scalars().all()
    return {"new_high_impact": len(rows), "since": last_seen.isoformat() + "Z"}
