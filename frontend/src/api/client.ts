import type {
  AssetOut,
  EconomicEvent,
  IntelPayload,
  MarketResponse,
  MoodResponse,
  NewsItem,
  SignalResponse,
} from "../types";

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function getJSON<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`HTTP ${r.status} on ${path}`);
  return (await r.json()) as T;
}

export function fetchNews(asset = "EURUSD", limit = 20) {
  return getJSON<{ items: NewsItem[] }>(`/news?asset=${asset}&limit=${limit}`);
}

export function fetchMarket(asset = "EURUSD", timeframe = "15m", limit = 96) {
  return getJSON<MarketResponse>(`/market?asset=${asset}&timeframe=${timeframe}&limit=${limit}`);
}

export function fetchSignal(asset = "EURUSD") {
  return getJSON<SignalResponse>(`/signal?asset=${asset}`);
}

export function fetchAssets() {
  return getJSON<{ items: AssetOut[] }>(`/assets`);
}

export function fetchMood() {
  return getJSON<MoodResponse>(`/mood`);
}

export function fetchEvents(hours = 48) {
  return getJSON<{ items: EconomicEvent[] }>(`/events?hours=${hours}`);
}

export function fetchIntel(asset = "EURUSD") {
  return getJSON<IntelPayload>(`/intel?asset=${asset}`);
}

export function fetchReplay(asset = "EURUSD") {
  return getJSON<{
    target: { id: number; title: string; published_at: string; sentiment: number; impact: string } | null;
    outcomes: {
      news_id: number;
      title: string;
      published_at: string;
      similarity: number;
      ret_15m: number | null;
      ret_1h: number | null;
      ret_4h: number | null;
    }[];
  }>(`/intel/replay?asset=${asset}`);
}

export const WS_URL = (() => {
  const u = new URL(BASE);
  u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
  u.pathname = "/realtime";
  return u.toString();
})();
