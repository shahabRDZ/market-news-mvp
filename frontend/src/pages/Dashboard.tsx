import { useCallback, useEffect, useRef, useState } from "react";
import { AdvancedIntelPanel } from "../components/AdvancedIntelPanel";
import { AssetCard } from "../components/AssetCard";
import { EventTimeline } from "../components/EventTimeline";
import { MarketMoodBanner } from "../components/MarketMoodBanner";
import { NewsList } from "../components/NewsList";
import { TodaysBriefCard } from "../components/TodaysBriefCard";
import { useI18n } from "../i18n";
import {
  fetchAssets,
  fetchEvents,
  fetchMarket,
  fetchMood,
  fetchNews,
  fetchSignal,
} from "../api/client";
import { useRealtime } from "../api/useRealtime";
import { useAuth } from "../auth/AuthContext";
import type {
  AssetOut,
  Candle,
  EconomicEvent,
  Indicators,
  MoodResponse,
  NewsItem,
  SignalResponse,
  WsFrame,
} from "../types";

type AssetState = {
  candles: Candle[];
  indicators: Indicators | null;
  signal: SignalResponse | null;
};

export function Dashboard() {
  const { user } = useAuth();
  const { t } = useI18n();
  const [assets, setAssets] = useState<AssetOut[]>([]);
  const [byAsset, setByAsset] = useState<Record<string, AssetState>>({});
  const [news, setNews] = useState<NewsItem[]>([]);
  const [mood, setMood] = useState<MoodResponse | null>(null);
  const [events, setEvents] = useState<EconomicEvent[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [connected, setConnected] = useState(false);
  const pollRef = useRef<number | undefined>(undefined);

  const loadAsset = useCallback(async (symbol: string) => {
    const [m, s] = await Promise.all([fetchMarket(symbol), fetchSignal(symbol)]);
    return { symbol, state: { candles: m.candles, indicators: m.indicators, signal: s } };
  }, []);

  const loadAll = useCallback(async () => {
    try {
      const assetsResp = await fetchAssets();
      setAssets(assetsResp.items);
      const [perAsset, n, mo, ev] = await Promise.all([
        Promise.all(assetsResp.items.map((a) => loadAsset(a.symbol))),
        fetchNews("EURUSD", 10),
        fetchMood(),
        fetchEvents(48),
      ]);
      const nextByAsset: Record<string, AssetState> = {};
      for (const r of perAsset) nextByAsset[r.symbol] = r.state;
      setByAsset(nextByAsset);
      setNews(n.items);
      setMood(mo);
      setEvents(ev.items);
      setLastUpdate(new Date());
    } catch {
      // keep previous state on transient errors
    }
  }, [loadAsset]);

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
      setByAsset((prev) => {
        const sym = frame.asset;
        const current = prev[sym] || { candles: [], indicators: null, signal: null };
        return { ...prev, [sym]: { ...current, signal: frame.payload } };
      });
    }
  }, []);
  useRealtime(onFrame);

  const secondsAgo = Math.max(0, Math.floor((Date.now() - lastUpdate.getTime()) / 1000));

  return (
    <main className="max-w-6xl mx-auto px-4 md:px-6 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-text_muted text-xs">live demo</div>
          <h1 className="text-xl font-semibold tracking-tight">Market Intelligence</h1>
        </div>
        <div className="text-xs text-text_muted">
          {user ? (
            <span className="me-3">
              plan: <span className="text-text_primary capitalize">{user.plan}</span>
            </span>
          ) : null}
          {connected ? t("status_live") : t("status_polling")} · {t("status_updated", { n: secondsAgo })}
        </div>
      </div>

      <TodaysBriefCard />

      <MarketMoodBanner mood={mood} />

      {assets[0] && <AdvancedIntelPanel asset={assets[0].symbol} />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
          {assets.map((a) => {
            const st = byAsset[a.symbol];
            return (
              <AssetCard
                key={a.symbol}
                asset={a.symbol}
                candles={st?.candles || []}
                indicators={st?.indicators || null}
                signal={st?.signal || null}
              />
            );
          })}
        </div>
        <div className="space-y-6">
          <div className="bg-surface border border-subtle rounded-lg p-5">
            <div className="text-text_secondary text-xs mb-3">Latest News</div>
            <NewsList items={news} />
          </div>
          <div className="bg-surface border border-subtle rounded-lg p-5">
            <div className="text-text_secondary text-xs mb-3">Coming Soon</div>
            <EventTimeline events={events} />
          </div>
        </div>
      </div>

      <p className="text-text_muted text-[11px] leading-relaxed">
        Informational only. Not investment advice. Probabilistic output may be wrong.
      </p>
    </main>
  );
}
