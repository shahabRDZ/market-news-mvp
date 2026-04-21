from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import get_db
from ..models import Asset, User, WatchlistItem
from ..services.plans import get_plan

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchlistOut(BaseModel):
    symbols: list[str]
    limit: int


class WatchlistPayload(BaseModel):
    symbol: str


@router.get("", response_model=WatchlistOut)
def get_watchlist(u: User = Depends(current_user), db: Session = Depends(get_db)) -> WatchlistOut:
    rows = db.execute(
        select(Asset.symbol).join(WatchlistItem, WatchlistItem.asset_id == Asset.id).where(WatchlistItem.user_id == u.id)
    ).scalars().all()
    return WatchlistOut(symbols=list(rows), limit=get_plan(u.plan).watchlist_limit)


@router.post("", response_model=WatchlistOut)
def add_watchlist(
    body: WatchlistPayload,
    u: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> WatchlistOut:
    plan = get_plan(u.plan)
    asset = db.execute(select(Asset).where(Asset.symbol == body.symbol)).scalar_one_or_none()
    if asset is None:
        raise HTTPException(404, "Asset not available")
    existing = db.execute(
        select(WatchlistItem).where(WatchlistItem.user_id == u.id, WatchlistItem.asset_id == asset.id)
    ).scalar_one_or_none()
    if existing is None:
        count = db.execute(select(WatchlistItem).where(WatchlistItem.user_id == u.id)).scalars().all()
        if len(count) >= plan.watchlist_limit:
            raise HTTPException(402, f"Watchlist limit of {plan.watchlist_limit} reached on plan {plan.name}")
        db.add(WatchlistItem(user_id=u.id, asset_id=asset.id))
        db.commit()
    return get_watchlist(u, db)


@router.delete("/{symbol}", response_model=WatchlistOut)
def remove_watchlist(
    symbol: str,
    u: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> WatchlistOut:
    asset = db.execute(select(Asset).where(Asset.symbol == symbol)).scalar_one_or_none()
    if asset is not None:
        row = db.execute(
            select(WatchlistItem).where(WatchlistItem.user_id == u.id, WatchlistItem.asset_id == asset.id)
        ).scalar_one_or_none()
        if row is not None:
            db.delete(row)
            db.commit()
    return get_watchlist(u, db)
