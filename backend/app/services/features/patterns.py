"""Pattern rule engine.

Rules is a JSON dict of key -> condition. Supported keys map to computed
features at evaluation time. Example:
    {
      "mood.label": "Risk-Off",
      "asset": "EURUSD",
      "direction": "DOWN",
      "impact_strength": "HIGH"
    }
A rule matches when all keys agree with the current state.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...models import Asset, Pattern, Signal
from ..plans import get_plan


SUPPORTED_KEYS = ["asset", "direction", "impact_strength", "mood.label", "min_probability"]


def evaluate(db: Session, user_id: int, mood_label: str) -> list[dict]:
    rows = db.execute(
        select(Pattern).where(Pattern.user_id == user_id, Pattern.active == True)
    ).scalars().all()
    matches: list[dict] = []
    latest_by_asset: dict[str, Signal] = {}
    for a in db.execute(select(Asset)).scalars().all():
        last = db.execute(
            select(Signal).where(Signal.asset_id == a.id).order_by(Signal.ts.desc()).limit(1)
        ).scalar_one_or_none()
        if last is not None:
            latest_by_asset[a.symbol] = last

    for p in rows:
        rules: dict[str, Any] = p.rules or {}
        asset = rules.get("asset")
        signals_to_check = [latest_by_asset[asset]] if asset in latest_by_asset else list(latest_by_asset.values())
        for sig in signals_to_check:
            sym = next((k for k, v in latest_by_asset.items() if v is sig), None)
            ok = True
            if "direction" in rules and sig.direction != rules["direction"]:
                ok = False
            if "impact_strength" in rules and sig.impact_strength != rules["impact_strength"]:
                ok = False
            if "mood.label" in rules and mood_label != rules["mood.label"]:
                ok = False
            if "min_probability" in rules:
                top = max(sig.prob_up, sig.prob_down, sig.prob_neutral)
                if top < float(rules["min_probability"]):
                    ok = False
            if ok:
                matches.append(
                    {
                        "pattern_id": p.id,
                        "pattern_name": p.name,
                        "asset": sym,
                        "direction": sig.direction,
                        "probability": max(sig.prob_up, sig.prob_down, sig.prob_neutral),
                        "matched_at": datetime.utcnow().isoformat() + "Z",
                    }
                )
                p.last_matched_at = datetime.utcnow()
                db.add(p)
    db.commit()
    return matches


def validate_rules(rules: dict) -> dict:
    cleaned = {}
    for k, v in (rules or {}).items():
        if k in SUPPORTED_KEYS:
            cleaned[k] = v
    return cleaned
