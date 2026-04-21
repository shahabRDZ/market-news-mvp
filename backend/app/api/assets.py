from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Asset
from ..schemas import AssetOut, AssetsResponse

router = APIRouter()


@router.get("/assets", response_model=AssetsResponse)
def list_assets(db: Session = Depends(get_db)) -> AssetsResponse:
    rows = db.execute(select(Asset).order_by(Asset.id.asc())).scalars().all()
    return AssetsResponse(items=[AssetOut(symbol=r.symbol, name=r.display_name) for r in rows])
