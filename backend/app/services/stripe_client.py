from __future__ import annotations

import logging

import stripe
from sqlalchemy.orm import Session

from ..config import settings
from ..models import User

log = logging.getLogger("stripe")


def _client() -> None:
    """Set the API key on the global stripe module. Safe to call repeatedly."""
    stripe.api_key = settings.STRIPE_SECRET_KEY


def get_or_create_customer(db: Session, user: User) -> str:
    _client()
    if user.stripe_customer_id:
        return user.stripe_customer_id
    customer = stripe.Customer.create(
        email=user.email,
        metadata={"user_id": str(user.id)},
    )
    user.stripe_customer_id = customer.id
    db.add(user)
    db.commit()
    db.refresh(user)
    return customer.id


def create_checkout_session(customer_id: str, price_id: str, user_id: int) -> str:
    _client()
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=settings.BILLING_SUCCESS_URL,
        cancel_url=settings.BILLING_CANCEL_URL,
        client_reference_id=str(user_id),
        allow_promotion_codes=True,
    )
    return session.url


def create_portal_session(customer_id: str) -> str:
    _client()
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=settings.BILLING_SUCCESS_URL,
    )
    return session.url


def verify_webhook(payload: bytes, signature: str) -> stripe.Event:
    _client()
    return stripe.Webhook.construct_event(
        payload=payload,
        sig_header=signature,
        secret=settings.STRIPE_WEBHOOK_SECRET,
    )


def plan_key_from_price(price_id: str | None) -> str | None:
    if not price_id:
        return None
    if price_id == settings.STRIPE_PRICE_PRO:
        return "pro"
    if price_id == settings.STRIPE_PRICE_PREMIUM:
        return "premium"
    if price_id == settings.STRIPE_PRICE_TEAM:
        return "team"
    if price_id == settings.STRIPE_PRICE_API:
        return "api"
    return None
