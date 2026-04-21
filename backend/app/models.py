from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(64))

    news = relationship("News", back_populates="asset")
    candles = relationship("Candle", back_populates="asset")
    signals = relationship("Signal", back_populates="asset")


class News(Base):
    __tablename__ = "news"
    __table_args__ = (UniqueConstraint("url_hash", name="uq_news_url_hash"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    source: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(512))
    url: Mapped[str] = mapped_column(String(1024))
    url_hash: Mapped[str] = mapped_column(String(64), index=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    sentiment: Mapped[float] = mapped_column(Float, default=0.0)
    impact: Mapped[str] = mapped_column(String(8), default="LOW")

    asset = relationship("Asset", back_populates="news")


class Candle(Base):
    __tablename__ = "candles"
    __table_args__ = (UniqueConstraint("asset_id", "timeframe", "ts", name="uq_candle"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    timeframe: Mapped[str] = mapped_column(String(8))
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)
    o: Mapped[float] = mapped_column(Float)
    h: Mapped[float] = mapped_column(Float)
    l: Mapped[float] = mapped_column(Float)
    c: Mapped[float] = mapped_column(Float)
    v: Mapped[float] = mapped_column(Float)

    asset = relationship("Asset", back_populates="candles")


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True, default=datetime.utcnow)
    direction: Mapped[str] = mapped_column(String(8))
    prob_up: Mapped[float] = mapped_column(Float)
    prob_down: Mapped[float] = mapped_column(Float)
    prob_neutral: Mapped[float] = mapped_column(Float)
    sentiment_score: Mapped[float] = mapped_column(Float)
    technical_score: Mapped[float] = mapped_column(Float)
    impact_strength: Mapped[str] = mapped_column(String(8))
    reason: Mapped[str] = mapped_column(String(256))
    details: Mapped[dict] = mapped_column(JSON, default=dict)

    asset = relationship("Asset", back_populates="signals")
