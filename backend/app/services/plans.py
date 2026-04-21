from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    key: str
    name: str
    price_monthly: int
    watchlist_limit: int
    api_calls_per_day: int
    ws_connections: int
    history_days: int
    realtime: bool
    llm_explanations: bool


PLANS: dict[str, Plan] = {
    "free": Plan("free", "Free", 0, 3, 0, 1, 1, False, False),
    "pro": Plan("pro", "Pro", 29, 15, 1000, 2, 90, True, False),
    "premium": Plan("premium", "Premium", 89, 50, 10000, 5, 730, True, True),
    "team": Plan("team", "Team", 249, 50, 25000, 25, 730, True, True),
    "api": Plan("api", "API", 499, 9999, 1000000, 100, 1825, True, True),
}


def get_plan(key: str) -> Plan:
    return PLANS.get(key, PLANS["free"])


def plan_allows(plan_key: str, feature: str) -> bool:
    plan = get_plan(plan_key)
    if feature == "realtime":
        return plan.realtime
    if feature == "llm":
        return plan.llm_explanations
    if feature == "api":
        return plan.api_calls_per_day > 0
    return True
