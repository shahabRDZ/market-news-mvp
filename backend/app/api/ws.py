from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.broadcaster import broadcaster

router = APIRouter()


@router.websocket("/realtime")
async def realtime(ws: WebSocket) -> None:
    await ws.accept()
    q = await broadcaster.subscribe()
    try:
        await ws.send_json({"type": "hello", "payload": {"version": 1}})
        while True:
            try:
                msg = await asyncio.wait_for(q.get(), timeout=20.0)
                await ws.send_json(msg)
            except asyncio.TimeoutError:
                await ws.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    finally:
        await broadcaster.unsubscribe(q)
