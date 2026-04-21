from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Asset, Signal
from ..schemas import MoodResponse

router = APIRouter()


@router.get("/mood", response_model=MoodResponse)
def mood(db: Session = Depends(get_db)) -> MoodResponse:
    assets = db.execute(select(Asset)).scalars().all()
    ups = downs = neutrals = 0
    strongest: tuple[str, str, float] | None = None  # (symbol, direction, magnitude)
    for a in assets:
        last = db.execute(
            select(Signal).where(Signal.asset_id == a.id).order_by(Signal.ts.desc()).limit(1)
        ).scalar_one_or_none()
        if last is None:
            continue
        if last.direction == "UP":
            ups += 1
        elif last.direction == "DOWN":
            downs += 1
        else:
            neutrals += 1
        mag = abs(last.sentiment_score) + abs(last.technical_score)
        if strongest is None or mag > strongest[2]:
            strongest = (a.symbol, last.direction, mag)

    total = max(1, ups + downs + neutrals)
    bull_ratio = ups / total
    bear_ratio = downs / total
    score = int(50 + (bull_ratio - bear_ratio) * 50)
    if score >= 65:
        label = "Risk-On"
    elif score <= 35:
        label = "Risk-Off"
    else:
        label = "Mixed"
    if strongest is None:
        summary = "Warming up, not enough signals yet"
    else:
        summary = f"{strongest[0]} leads {strongest[1].lower()} move"
    return MoodResponse(label=label, score=score, summary=summary)
