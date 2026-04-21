import type { Candle, Indicators, SignalResponse } from "../types";
import { SentimentBar } from "./SentimentBar";
import { ProbabilityBar } from "./ProbabilityBar";
import { PriceMini } from "./PriceMini";

type Props = {
  asset: string;
  candles: Candle[];
  indicators: Indicators | null;
  signal: SignalResponse | null;
};

const TREND_GLYPH: Record<string, string> = { up: "▲", down: "▼", flat: "≈" };
const TREND_COLOR: Record<string, string> = { up: "text-up", down: "text-down", flat: "text-neutral" };
const DIRECTION_COLOR: Record<string, string> = {
  UP: "text-up",
  DOWN: "text-down",
  NEUTRAL: "text-neutral",
};

export function AssetCard({ asset, candles, indicators, signal }: Props) {
  const last = candles.at(-1)?.c;
  const trend = indicators?.trend || "flat";
  return (
    <div className="bg-surface border border-subtle rounded-lg p-5 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-text_secondary text-xs">{asset}</div>
          <div className="flex items-baseline gap-3">
            <div className="num text-3xl text-text_primary">
              {last !== undefined ? last.toFixed(5) : "—"}
            </div>
            <div className={`text-sm ${TREND_COLOR[trend]}`}>
              {TREND_GLYPH[trend]} {trend}
            </div>
          </div>
        </div>
        {signal && (
          <div className="text-right">
            <div className={`text-sm font-semibold ${DIRECTION_COLOR[signal.direction]}`}>
              {signal.direction}
            </div>
            <div className="num text-xs text-text_muted">
              {Math.round(
                signal.probabilities[
                  signal.direction.toLowerCase() as "up" | "down" | "neutral"
                ] * 100,
              )}
              %
            </div>
          </div>
        )}
      </div>

      {signal && <SentimentBar value={signal.sentiment_score} />}
      {signal && <ProbabilityBar probs={signal.probabilities} />}

      {signal && (
        <div className="text-xs text-text_secondary italic">"{signal.reason}"</div>
      )}

      <PriceMini candles={candles} />

      {indicators && (
        <div className="grid grid-cols-3 gap-2 text-xs text-text_secondary">
          <div className="flex flex-col">
            <span className="text-text_muted">RSI</span>
            <span className="num text-text_primary">{indicators.rsi.toFixed(1)}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-text_muted">MA20</span>
            <span className="num text-text_primary">{indicators.ma20.toFixed(5)}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-text_muted">MA50</span>
            <span className="num text-text_primary">{indicators.ma50.toFixed(5)}</span>
          </div>
        </div>
      )}
    </div>
  );
}
