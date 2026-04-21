import type { MarketResponse, NewsItem, SignalResponse } from "../types";

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

export const WS_URL = (() => {
  const u = new URL(BASE);
  u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
  u.pathname = "/realtime";
  return u.toString();
})();
