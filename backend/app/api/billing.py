from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..config import settings
from ..db import get_db
from ..models import User
from ..services import stripe_client
from ..services.plans import PLANS

log = logging.getLogger("billing")
router = APIRouter(prefix="/billing", tags=["billing"])


class PlansResponse(BaseModel):
    plans: list[dict]
    stripe_enabled: bool


class SelectPlanPayload(BaseModel):
    plan: str


class CheckoutResponse(BaseModel):
    url: str


@router.get("/plans", response_model=PlansResponse)
def list_plans() -> PlansResponse:
    return PlansResponse(
        stripe_enabled=settings.stripe_enabled,
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
        ],
    )


@router.post("/select")
def select_plan(
    body: SelectPlanPayload,
    u: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Dev-mode plan switch (no payment). Used when Stripe isn't configured,
    and for downgrading to free.
    """
    if body.plan not in PLANS:
        raise HTTPException(400, "Unknown plan")
    if settings.stripe_enabled and body.plan != "free":
        raise HTTPException(400, "Use /billing/checkout for paid plans when Stripe is enabled")
    u.plan = body.plan
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"plan": u.plan}


@router.post("/checkout", response_model=CheckoutResponse)
def checkout(
    body: SelectPlanPayload,
    u: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> CheckoutResponse:
    if not settings.stripe_enabled:
        raise HTTPException(400, "Stripe is not configured on this server")
    if body.plan not in PLANS or body.plan == "free":
        raise HTTPException(400, "Unknown or non-billable plan")
    price_id = settings.stripe_price_for(body.plan)
    if not price_id:
        raise HTTPException(400, f"No Stripe price ID configured for plan '{body.plan}'")
    customer_id = stripe_client.get_or_create_customer(db, u)
    url = stripe_client.create_checkout_session(customer_id, price_id, u.id)
    return CheckoutResponse(url=url)


@router.post("/portal", response_model=CheckoutResponse)
def portal(
    u: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> CheckoutResponse:
    if not settings.stripe_enabled:
        raise HTTPException(400, "Stripe is not configured on this server")
    if not u.stripe_customer_id:
        raise HTTPException(400, "No active subscription on this account")
    url = stripe_client.create_portal_session(u.stripe_customer_id)
    return CheckoutResponse(url=url)


@router.post("/webhook", include_in_schema=False)
async def webhook(
    request: Request,
    stripe_signature: str = Header(default="", alias="Stripe-Signature"),
    db: Session = Depends(get_db),
) -> dict:
    if not settings.stripe_enabled or not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(400, "Stripe webhook not configured")
    payload = await request.body()
    try:
        event = stripe_client.verify_webhook(payload, stripe_signature)
    except Exception as exc:
        log.warning("invalid stripe webhook signature: %s", exc)
        raise HTTPException(400, "Invalid webhook signature")

    etype = event["type"]
    obj = event["data"]["object"]

    if etype == "checkout.session.completed":
        user_id = obj.get("client_reference_id")
        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription")
        if not user_id:
            return {"ok": True, "ignored": "no client_reference_id"}
        u = db.get(User, int(user_id))
        if u is None:
            return {"ok": True, "ignored": "user not found"}
        u.stripe_customer_id = customer_id or u.stripe_customer_id
        u.stripe_subscription_id = subscription_id or u.stripe_subscription_id
        db.add(u)
        db.commit()
        return {"ok": True}

    if etype in ("customer.subscription.created", "customer.subscription.updated"):
        customer_id = obj.get("customer")
        subscription_id = obj.get("id")
        items = (obj.get("items") or {}).get("data") or []
        price_id = items[0]["price"]["id"] if items else None
        plan_key = stripe_client.plan_key_from_price(price_id)
        status = obj.get("status")
        u = db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        ).scalar_one_or_none()
        if u is None:
            return {"ok": True, "ignored": "no user for customer"}
        if plan_key and status in ("active", "trialing"):
            u.plan = plan_key
            u.stripe_subscription_id = subscription_id
        elif status in ("canceled", "incomplete_expired", "unpaid"):
            u.plan = "free"
            u.stripe_subscription_id = None
        db.add(u)
        db.commit()
        return {"ok": True}

    if etype == "customer.subscription.deleted":
        customer_id = obj.get("customer")
        u = db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        ).scalar_one_or_none()
        if u is not None:
            u.plan = "free"
            u.stripe_subscription_id = None
            db.add(u)
            db.commit()
        return {"ok": True}

    return {"ok": True, "ignored": etype}
