"""Near-realtime market poller.

First tries Coinbase/Binance WebSocket for true streaming. If those TLS
handshakes fail (common on restrictive networks), falls back to fast polling
of Yahoo Finance's public chart endpoint which works from most places. The
endpoint is the same one yfinance uses under the hood but called directly so
we can poll every few seconds instead of every minute.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime

import httpx
import websockets
from sqlalchemy import select

from ..db import SessionLocal
from ..models import Asset, Candle
from .broadcaster import broadcaster

log = logging.getLogger("crypto_ws")

INTERNAL = ["BTCUSD", "ETHUSD"]
YAHOO_SYMBOL = {"BTCUSD": "BTC-USD", "ETHUSD": "ETH-USD"}
COINBASE_PRODUCT = {"BTCUSD": "BTC-USD", "ETHUSD": "ETH-USD"}
BINANCE_STREAM = {"BTCUSD": "btcusdt", "ETHUSD": "ethusdt"}

COINBASE_URL = "wss://ws-feed.exchange.coinbase.com"
YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1m&range=1d"

POLL_SECONDS = 5


def _asset_ids() -> dict[str, int]:
    out: dict[str, int] = {}
    with SessionLocal() as db:
        for sym in INTERNAL:
            a = db.execute(select(Asset).where(Asset.symbol == sym)).scalar_one_or_none()
            if a is not None:
                out[sym] = a.id
    return out


def _apply_tick(asset_id: int, price: float, volume: float = 0.0, ts: datetime | None = None) -> None:
    ts = ts or datetime.utcnow()
    minute = ts.replace(second=0, microsecond=0)
    with SessionLocal() as db:
        row = db.execute(
            select(Candle).where(Candle.asset_id == asset_id, Candle.timeframe == "1m", Candle.ts == minute)
        ).scalar_one_or_none()
        if row is None:
            row = Candle(
                asset_id=asset_id, timeframe="1m", ts=minute,
                o=price, h=price, l=price, c=price, v=volume,
            )
        else:
            row.h = max(row.h, price)
            row.l = min(row.l, price)
            row.c = price
            row.v += volume
        db.add(row)
        db.commit()


async def _publish_tick(symbol: str, price: float, source: str) -> None:
    await broadcaster.publish(
        {
            "type": "market.tick",
            "asset": symbol,
            "payload": {
                "ts": datetime.utcnow().isoformat() + "Z",
                "c": price,
                "source": source,
            },
        }
    )


async def _try_coinbase_ws(stop: asyncio.Event, ids: dict[str, int]) -> bool:
    product_ids = [COINBASE_PRODUCT[s] for s in ids if s in COINBASE_PRODUCT]
    reverse = {v: k for k, v in COINBASE_PRODUCT.items()}
    try:
        async with websockets.connect(
            COINBASE_URL, ping_interval=20, ping_timeout=20, max_size=2**20, close_timeout=5,
            open_timeout=6,
        ) as ws:
            await ws.send(json.dumps(
                {"type": "subscribe", "channels": [{"name": "ticker", "product_ids": product_ids}]}
            ))
            log.info("coinbase WS live")
            async for raw in ws:
                if stop.is_set():
                    return True
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue
                if msg.get("type") != "ticker":
                    continue
                product = msg.get("product_id")
                internal = reverse.get(product)
                if not internal or internal not in ids:
                    continue
                try:
                    price = float(msg.get("price"))
                    vol = float(msg.get("last_size") or 0.0)
                except (TypeError, ValueError):
                    continue
                _apply_tick(ids[internal], price, vol)
                await _publish_tick(internal, price, "coinbase")
    except Exception as exc:
        log.warning("coinbase WS error: %s", exc)
        return False
    return True


async def _try_binance_ws(stop: asyncio.Event, ids: dict[str, int]) -> bool:
    stream = "/".join(f"{BINANCE_STREAM[s]}@kline_1m" for s in ids if s in BINANCE_STREAM)
    url = f"wss://stream.binance.com:9443/stream?streams={stream}"
    reverse = {v: k for k, v in BINANCE_STREAM.items()}
    try:
        async with websockets.connect(url, ping_interval=20, ping_timeout=20, max_size=2**20, open_timeout=6) as ws:
            log.info("binance WS live")
            async for raw in ws:
                if stop.is_set():
                    return True
                try:
                    msg = json.loads(raw)
                except Exception:
                    continue
                data = msg.get("data") or msg
                k = data.get("k") or {}
                stream_sym = (data.get("s") or "").lower()
                internal = reverse.get(stream_sym)
                if not internal or internal not in ids or not k:
                    continue
                try:
                    price = float(k.get("c", 0))
                except (TypeError, ValueError):
                    continue
                _apply_tick(ids[internal], price, float(k.get("v", 0) or 0.0))
                await _publish_tick(internal, price, "binance")
    except Exception as exc:
        log.warning("binance WS error: %s", exc)
        return False
    return True


async def _yahoo_poll_loop(stop: asyncio.Event, ids: dict[str, int]) -> None:
    log.info("using yahoo fast-poll every %ds", POLL_SECONDS)
    headers = {"User-Agent": "Mozilla/5.0"}
    async with httpx.AsyncClient(timeout=6.0, headers=headers) as client:
        while not stop.is_set():
            for internal, asset_id in ids.items():
                sym = YAHOO_SYMBOL.get(internal)
                if not sym:
                    continue
                try:
                    r = await client.get(YAHOO_URL.format(sym=sym))
                    if r.status_code != 200:
                        continue
                    data = r.json()
                    result = (data.get("chart") or {}).get("result") or []
                    if not result:
                        continue
                    meta = result[0].get("meta") or {}
                    price = float(meta.get("regularMarketPrice") or 0)
                    if price <= 0:
                        continue
                    _apply_tick(asset_id, price)
                    await _publish_tick(internal, price, "yahoo")
                except Exception as exc:
                    log.debug("yahoo poll %s fail: %s", internal, exc)
            try:
                await asyncio.wait_for(stop.wait(), timeout=POLL_SECONDS)
            except asyncio.TimeoutError:
                pass


async def _run(stop: asyncio.Event) -> None:
    ids = _asset_ids()
    if not ids:
        log.warning("no crypto assets; stream disabled")
        return

    for name, fn in [("coinbase", _try_coinbase_ws), ("binance", _try_binance_ws)]:
        if stop.is_set():
            return
        log.info("trying %s WS...", name)
        clean = await fn(stop, ids)
        if clean:
            return

    await _yahoo_poll_loop(stop, ids)


_stop_event: asyncio.Event | None = None
_task: asyncio.Task | None = None


def start(loop: asyncio.AbstractEventLoop) -> None:
    global _stop_event, _task
    _stop_event = asyncio.Event()
    _task = loop.create_task(_run(_stop_event))


async def stop() -> None:
    global _stop_event, _task
    if _stop_event is not None:
        _stop_event.set()
    if _task is not None:
        try:
            await asyncio.wait_for(_task, timeout=5.0)
        except asyncio.TimeoutError:
            _task.cancel()
