export type NewsItem = {
  id: number;
  source: string;
  title: string;
  url: string;
  published_at: string;
  sentiment: number;
  impact: "LOW" | "MED" | "HIGH";
};

export type Candle = {
  ts: string;
  o: number;
  h: number;
  l: number;
  c: number;
  v: number;
};

export type Indicators = {
  rsi: number;
  ma20: number;
  ma50: number;
  trend: "up" | "down" | "flat";
};

export type MarketResponse = {
  asset: string;
  timeframe: string;
  candles: Candle[];
  indicators: Indicators | null;
};

export type Probabilities = { up: number; down: number; neutral: number };

export type SignalResponse = {
  asset: string;
  ts: string;
  probabilities: Probabilities;
  direction: "UP" | "DOWN" | "NEUTRAL";
  sentiment_score: number;
  technical_score: number;
  impact_strength: "LOW" | "MED" | "HIGH";
  reason: string;
};

export type EconomicEvent = {
  id: number;
  kind: string;
  country: string;
  importance: 1 | 2 | 3;
  event_time: string;
  forecast: number | null;
  previous: number | null;
  actual: number | null;
  affected_assets: string[];
  anticipation: number;
};

export type MoodResponse = {
  label: "Risk-On" | "Risk-Off" | "Mixed";
  score: number;
  summary: string;
};

export type AssetOut = { symbol: string; name: string };

export type IntelPayload = {
  asset: string;
  ts: string;
  market_state: "LOW" | "MEDIUM" | "HIGH";
  stress: {
    score: number;
    level: "LOW" | "MEDIUM" | "HIGH";
    compression_ratio: number;
    range_ratio: number;
    reason: string;
  };
  liquidity_zones: { level: number; side: "above" | "below"; touches: number; distance_pct: number }[];
  smart_money_flow: {
    flow: "INFLOW" | "OUTFLOW" | "BALANCED";
    score: number;
    trap_probability: number;
    notes: string[];
  };
  contradiction: {
    flagged: boolean;
    direction: "opposite" | "aligned" | "unclear";
    news_bias: number;
    price_return: number;
    note: string;
  };
  pre_news: {
    minutes_to_event: number;
    anticipation: number;
    pressure: number;
    fake_move_risk: "LOW" | "MED" | "HIGH";
    note: string;
    event_kind: string | null;
  };
  explanation: string;
};

export type WsFrame =
  | { type: "hello"; payload: { version: number } }
  | { type: "ping" }
  | { type: "news.new"; asset: string; payload: NewsItem }
  | { type: "signal.updated"; asset: string; payload: SignalResponse };
