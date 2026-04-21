"""Paper Bet feature: users place directional bets, system resolves at horizon,
per-user accuracy and streak tracked.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import Asset, Candle, PaperBet, User


def place(db: Session, user: User, asset_symbol: str, direction: str, horizon_minutes: int = 60) -> PaperBet:
    asset = db.execute(select(Asset).where(Asset.symbol == asset_symbol)).scalar_one_or_none()
    if asset is None:
        raise ValueError("asset not found")
    last = db.execute(
        select(Candle).where(Candle.asset_id == asset.id).order_by(Candle.ts.desc()).limit(1)
    ).scalar_one_or_none()
    if last is None:
        raise ValueError("no price available")
    bet = PaperBet(
        user_id=user.id,
        asset_symbol=asset_symbol,
        direction=direction.upper(),
        horizon_minutes=horizon_minutes,
        placed_at=datetime.utcnow(),
        resolve_at=datetime.utcnow() + timedelta(minutes=horizon_minutes),
        placed_price=float(last.c),
    )
    db.add(bet)
    db.commit()
    db.refresh(bet)
    return bet


def resolve_due(db: Session) -> int:
    now = datetime.utcnow()
    due = db.execute(
        select(PaperBet).where(PaperBet.resolved == False, PaperBet.resolve_at <= now)
    ).scalars().all()
    resolved = 0
    for bet in due:
        asset = db.execute(select(Asset).where(Asset.symbol == bet.asset_symbol)).scalar_one_or_none()
        if asset is None:
            bet.resolved = True
            continue
        current = db.execute(
            select(Candle).where(Candle.asset_id == asset.id).order_by(Candle.ts.desc()).limit(1)
        ).scalar_one_or_none()
        if current is None:
            continue
        rr = (current.c - bet.placed_price) / bet.placed_price
        bet.realized_return = float(rr)
        if bet.direction == "UP":
            bet.correct = rr > 0
        elif bet.direction == "DOWN":
            bet.correct = rr < 0
        else:
            bet.correct = abs(rr) < 0.001
        bet.resolved = True
        db.add(bet)
        resolved += 1
    if resolved:
        db.commit()
    return resolved


def stats(db: Session, user: User) -> dict:
    all_bets = db.execute(
        select(PaperBet).where(PaperBet.user_id == user.id).order_by(PaperBet.placed_at.desc())
    ).scalars().all()
    resolved = [b for b in all_bets if b.resolved and b.correct is not None]
    if not resolved:
        return {"placed": len(all_bets), "resolved": 0, "accuracy": None, "streak": 0, "recent": []}
    correct = sum(1 for b in resolved if b.correct)
    # current streak from most recent resolved bet
    streak = 0
    expected = None
    for b in resolved:
        if expected is None:
            expected = b.correct
            streak = 1
            continue
        if b.correct == expected:
            streak += 1
        else:
            break
    return {
        "placed": len(all_bets),
        "resolved": len(resolved),
        "accuracy": round(correct / len(resolved), 3),
        "streak": streak if expected else -streak,
        "recent": [
            {
                "asset": b.asset_symbol,
                "direction": b.direction,
                "correct": b.correct,
                "return": round(b.realized_return or 0.0, 5),
                "placed_at": b.placed_at.isoformat() + "Z",
            }
            for b in all_bets[:10]
        ],
    }
