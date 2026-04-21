from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from .api import market, news, signal, ws
from .config import settings
from .db import Base, SessionLocal, engine
from .models import Asset
from .workers.scheduler import build_scheduler, job_fetch_market, job_fetch_news

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def _seed_assets() -> None:
    with SessionLocal() as db:
        defaults = [("EURUSD", "EUR/USD"), ("BTCUSD", "Bitcoin / USD"), ("XAUUSD", "Gold / USD")]
        for sym, name in defaults:
            existing = db.execute(select(Asset).where(Asset.symbol == sym)).scalar_one_or_none()
            if existing is None:
                db.add(Asset(symbol=sym, display_name=name))
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _seed_assets()
    scheduler = build_scheduler()
    scheduler.start()
    # Kick off an immediate first run so the UI has data right away.
    try:
        await job_fetch_news("EURUSD")
    except Exception as exc:
        logging.warning("initial news fetch failed: %s", exc)
    try:
        await job_fetch_market("EURUSD")
    except Exception as exc:
        logging.warning("initial market fetch failed: %s", exc)
    app.state.scheduler = scheduler
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title="Market News Intelligence MVP", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True, "mock": settings.use_mock}


app.include_router(news.router)
app.include_router(market.router)
app.include_router(signal.router)
app.include_router(ws.router)
