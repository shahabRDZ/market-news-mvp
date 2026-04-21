from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Asset, News
from ..schemas import NewsItem, NewsList

router = APIRouter()


@router.get("/news", response_model=NewsList)
def list_news(
    asset: str = Query("EURUSD"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
) -> NewsList:
    a = db.execute(select(Asset).where(Asset.symbol == asset)).scalar_one_or_none()
    if a is None:
        return NewsList(items=[])
    rows = db.execute(
        select(News).where(News.asset_id == a.id).order_by(News.published_at.desc()).limit(limit)
    ).scalars().all()
    return NewsList(
        items=[
            NewsItem(
                id=r.id,
                source=r.source,
                title=r.title,
                url=r.url,
                published_at=r.published_at,
                sentiment=r.sentiment,
                impact=r.impact,
            )
            for r in rows
        ]
    )
