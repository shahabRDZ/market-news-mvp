import { useCallback, useEffect, useRef, useState } from "react";
import { AssetCard } from "../components/AssetCard";
import { NewsList } from "../components/NewsList";
import { fetchMarket, fetchNews, fetchSignal } from "../api/client";
import { useRealtime } from "../api/useRealtime";
import { useAuth } from "../auth/AuthContext";
import type { Candle, Indicators, NewsItem, SignalResponse, WsFrame } from "../types";

const ASSET = "EURUSD";

export function Dashboard() {
  const { user } = useAuth();
  const [candles, setCandles] = useState<Candle[]>([]);
  const [indicators, setIndicators] = useState<Indicators | null>(null);
  const [signal, setSignal] = useState<SignalResponse | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [connected, setConnected] = useState(false);
  const pollRef = useRef<number | undefined>(undefined);

  const loadAll = useCallback(async () => {
    try {
      const [m, s, n] = await Promise.all([
        fetchMarket(ASSET),
        fetchSignal(ASSET),
        fetchNews(ASSET, 10),
      ]);
      setCandles(m.candles);
      setIndicators(m.indicators);
      setSignal(s);
      setNews(n.items);
      setLastUpdate(new Date());
    } catch {
      // keep previous state on transient errors
    }
  }, []);

  useEffect(() => {
    loadAll();
    pollRef.current = window.setInterval(loadAll, 15000);
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [loadAll]);

  const onFrame = useCallback((frame: WsFrame) => {
    setConnected(true);
    setLastUpdate(new Date());
    if (frame.type === "news.new") {
      setNews((prev) => {
        if (prev.some((p) => p.id === frame.payload.id)) return prev;
        return [frame.payload, ...prev].slice(0, 10);
      });
    } else if (frame.type === "signal.updated") {
      setSignal(frame.payload);
    }
  }, []);
  useRealtime(onFrame);

  const secondsAgo = Math.max(0, Math.floor((Date.now() - lastUpdate.getTime()) / 1000));

  return (
    <main className="max-w-6xl mx-auto px-4 md:px-6 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="text-text_muted text-xs">live demo</div>
          <h1 className="text-xl font-semibold tracking-tight">{ASSET}</h1>
        </div>
        <div className="text-xs text-text_muted">
          {user ? (
            <span className="mr-3">
              plan: <span className="text-text_primary capitalize">{user.plan}</span>
            </span>
          ) : null}
          {connected ? "live" : "polling"} · updated {secondsAgo}s ago
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <AssetCard asset={ASSET} candles={candles} indicators={indicators} signal={signal} />
        </div>
        <div className="bg-surface border border-subtle rounded-lg p-5">
          <div className="text-text_secondary text-xs mb-3">Latest News</div>
          <NewsList items={news} />
        </div>
      </div>

      <p className="text-text_muted text-[11px] mt-10 leading-relaxed">
        Informational only. Not investment advice. Probabilistic output may be wrong.
      </p>
    </main>
  );
}
