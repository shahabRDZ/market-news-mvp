from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Asset, News
from . import rss_fetcher
from .sentiment import count_keywords, impact_class, score

MOCK_PATH = Path(__file__).resolve().parent.parent / "data" / "mock_news.json"


def _hash(url: str, title: str) -> str:
    return hashlib.sha256(f"{url}|{title}".encode("utf-8")).hexdigest()


def _parse_dt(value: str) -> datetime:
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(value).astimezone(timezone.utc).replace(tzinfo=None)
    except ValueError:
        return datetime.utcnow()


def _load_mock() -> list[dict[str, Any]]:
    raw = json.loads(MOCK_PATH.read_text())
    now = datetime.utcnow()
    items = []
    for i, entry in enumerate(raw):
        items.append(
            {
                "source": entry.get("source", "Mock"),
                "title": entry["title"],
                "url": entry.get("url", f"https://example.com/mock/{i}"),
                "published_at": now - timedelta(minutes=i * 7),
            }
        )
    return items


def _fetch_from_newsapi(query: str) -> list[dict[str, Any]]:
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 30,
        "apiKey": settings.NEWSAPI_KEY,
    }
    with httpx.Client(timeout=10.0) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    items = []
    for a in data.get("articles", []):
        items.append(
            {
                "source": (a.get("source") or {}).get("name", "NewsAPI"),
                "title": a.get("title") or "",
                "url": a.get("url") or "",
                "published_at": _parse_dt(a.get("publishedAt") or datetime.utcnow().isoformat()),
            }
        )
    return items


def fetch_and_store(db: Session, asset_symbol: str = "EURUSD") -> list[News]:
    asset = db.execute(select(Asset).where(Asset.symbol == asset_symbol)).scalar_one_or_none()
    if asset is None:
        return []

    query = "EUR OR USD OR ECB OR Fed OR CPI OR inflation OR rate"
    raw_items: list[dict[str, Any]] = []
    if settings.NEWSAPI_KEY:
        try:
            raw_items = _fetch_from_newsapi(query)
        except Exception:
            raw_items = []
    if not raw_items:
        # No key, or NewsAPI failed. Try real RSS feeds (no key needed).
        try:
            raw_items = rss_fetcher.fetch_all()
        except Exception:
            raw_items = []
    if not raw_items:
        # Last resort: static mock so UI always has something.
        raw_items = _load_mock()

    inserted: list[News] = []
    for item in raw_items:
        title = item["title"]
        if not title:
            continue
        url_hash = _hash(item["url"], title)
        exists = db.execute(select(News).where(News.url_hash == url_hash)).scalar_one_or_none()
        if exists:
            continue
        s = score(title)
        impact = impact_class(s, count_keywords(title))
        row = News(
            asset_id=asset.id,
            source=item["source"][:64],
            title=title[:512],
            url=item["url"][:1024],
            url_hash=url_hash,
            published_at=item["published_at"],
            sentiment=s,
            impact=impact,
        )
        db.add(row)
        inserted.append(row)
    if inserted:
        db.commit()
        for row in inserted:
            db.refresh(row)
    return inserted
