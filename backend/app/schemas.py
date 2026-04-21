from datetime import datetime

from pydantic import BaseModel


class NewsItem(BaseModel):
    id: int
    source: str
    title: str
    url: str
    published_at: datetime
    sentiment: float
    impact: str


class NewsList(BaseModel):
    items: list[NewsItem]


class Candle(BaseModel):
    ts: datetime
    o: float
    h: float
    l: float
    c: float
    v: float


class Indicators(BaseModel):
    rsi: float
    ma20: float
    ma50: float
    trend: str


class MarketResponse(BaseModel):
    asset: str
    timeframe: str
    candles: list[Candle]
    indicators: Indicators | None = None


class Probabilities(BaseModel):
    up: float
    down: float
    neutral: float


class EconomicEventOut(BaseModel):
    id: int
    kind: str
    country: str
    importance: int
    event_time: datetime
    forecast: float | None = None
    previous: float | None = None
    actual: float | None = None
    affected_assets: list[str] = []
    anticipation: int = 0


class EventsResponse(BaseModel):
    items: list[EconomicEventOut]


class AssetOut(BaseModel):
    symbol: str
    name: str


class AssetsResponse(BaseModel):
    items: list[AssetOut]


class MoodResponse(BaseModel):
    label: str
    score: int
    summary: str


class SignalResponse(BaseModel):
    asset: str
    ts: datetime
    probabilities: Probabilities
    direction: str
    sentiment_score: float
    technical_score: float
    impact_strength: str
    reason: str
