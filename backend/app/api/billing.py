from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import get_db
from ..models import User
from ..services.plans import PLANS

router = APIRouter(prefix="/billing", tags=["billing"])


class PlansResponse(BaseModel):
    plans: list[dict]


class SelectPlanPayload(BaseModel):
    plan: str


@router.get("/plans", response_model=PlansResponse)
def list_plans() -> PlansResponse:
    return PlansResponse(
        plans=[
            {
                "key": p.key,
                "name": p.name,
                "price_monthly": p.price_monthly,
                "watchlist_limit": p.watchlist_limit,
                "api_calls_per_day": p.api_calls_per_day,
                "ws_connections": p.ws_connections,
                "history_days": p.history_days,
                "realtime": p.realtime,
                "llm_explanations": p.llm_explanations,
            }
            for p in PLANS.values()
        ]
    )


@router.post("/select")
def select_plan(
    body: SelectPlanPayload,
    u: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """MVP: no real payment. Real Stripe integration slots in here.
    Enterprise tier ("api") still selectable in dev for testing API access.
    """
    if body.plan not in PLANS:
        raise HTTPException(400, "Unknown plan")
    u.plan = body.plan
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"plan": u.plan, "note": "Dev-mode plan switch. Stripe checkout not wired in MVP."}
