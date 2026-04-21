"""Real news ingestion via RSS.

No API key required. Works globally, no quotas. Used automatically when
NEWSAPI_KEY is missing, so the app can ship real news out of the box.
"""
from __future__ import annotations

import asyncio
import concurrent.futures
from datetime import datetime, timezone
from typing import Any

import feedparser

FEEDS: list[tuple[str, str]] = [
    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
    ("CNBC Markets", "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
    ("Investing.com", "https://www.investing.com/rss/news_25.rss"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("ForexLive", "https://www.forexlive.com/feed/news"),
    ("FXStreet", "https://www.fxstreet.com/rss/news"),
    ("MarketWatch Top", "https://feeds.marketwatch.com/marketwatch/topstories/"),
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
]


def _parse_one(source: str, url: str) -> list[dict[str, Any]]:
    d = feedparser.parse(url)
    items: list[dict[str, Any]] = []
    for entry in d.entries[:20]:
        title = (entry.get("title") or "").strip()
        if not title:
            continue
        link = entry.get("link") or ""
        published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if published_parsed:
            published = datetime.fromtimestamp(
                __import__("calendar").timegm(published_parsed), tz=timezone.utc
            ).replace(tzinfo=None)
        else:
            published = datetime.utcnow()
        items.append(
            {
                "source": source,
                "title": title,
                "url": link,
                "published_at": published,
            }
        )
    return items


def fetch_all() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(FEEDS)) as pool:
        futs = {pool.submit(_parse_one, s, u): s for s, u in FEEDS}
        for fut in concurrent.futures.as_completed(futs, timeout=20):
            try:
                out.extend(fut.result())
            except Exception:
                continue
    # Newest first.
    out.sort(key=lambda x: x["published_at"], reverse=True)
    return out[:60]
