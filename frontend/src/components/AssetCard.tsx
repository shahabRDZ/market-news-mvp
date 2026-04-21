import type { Candle, Indicators, SignalResponse } from "../types";
import { useI18n } from "../i18n";
import { en } from "../i18n/en";
import { fa } from "../i18n/fa";
import { humanizeDirection, humanizeRsi, humanizeSentiment, humanizeTrend } from "../i18n/humanize";
import { SentimentBar } from "./SentimentBar";
import { ProbabilityBar } from "./ProbabilityBar";
import { PriceMini } from "./PriceMini";
import { Tooltip } from "./Tooltip";

type Props = {
  asset: string;
  candles: Candle[];
  indicators: Indicators | null;
  signal: SignalResponse | null;
};

const TREND_GLYPH: Record<string, string> = { up: "▲", down: "▼", flat: "≈" };
const TREND_COLOR: Record<string, string> = { up: "text-up", down: "text-down", flat: "text-neutral" };
const DIRECTION_COLOR: Record<string, string> = { UP: "text-up", DOWN: "text-down", NEUTRAL: "text-neutral" };

export function AssetCard({ asset, candles, indicators, signal }: Props) {
  const { t, lang, plain } = useI18n();
  const dict = lang === "fa" ? fa : en;
  const last = candles.at(-1)?.c;
  const trend = indicators?.trend || "flat";

  const directionLabel =
    signal &&
    (signal.direction === "UP" ? t("asset_up") : signal.direction === "DOWN" ? t("asset_down") : t("asset_neutral"));

  return (
    <div className="bg-surface border border-subtle rounded-lg p-5 space-y-4">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-text_secondary text-xs">{asset}</div>
          <div className="flex items-baseline gap-3">
            <div className="num text-3xl text-text_primary">
              {last !== undefined ? last.toFixed(last > 100 ? 2 : 5) : "—"}
            </div>
            <div className={`text-sm ${TREND_COLOR[trend]}`}>
              {TREND_GLYPH[trend]} {plain ? humanizeTrend(trend, dict) : t((`asset_trend_${trend}`) as any)}
            </div>
          </div>
        </div>
        {signal && (
          <div className="text-end">
            <div className={`text-sm font-semibold ${DIRECTION_COLOR[signal.direction]}`}>
              {plain ? humanizeDirection(signal.direction, dict) : directionLabel}
            </div>
            <div className="num text-xs text-text_muted">
              {Math.round(
                signal.probabilities[signal.direction.toLowerCase() as "up" | "down" | "neutral"] * 100,
              )}
              %
            </div>
          </div>
        )}
      </div>

      {signal && (
        <>
          <Tooltip content={t("tip_sentiment")}>
            <span className="text-[11px] text-text_muted">
              {plain ? humanizeSentiment(signal.sentiment_score, dict) : t("asset_sentiment")}
            </span>
          </Tooltip>
          <SentimentBar value={signal.sentiment_score} />
          <ProbabilityBar probs={signal.probabilities} />
          <div className="text-xs text-text_secondary italic">"{signal.reason}"</div>
        </>
      )}

      <PriceMini candles={candles} />

      {indicators && (
        <div className="grid grid-cols-3 gap-2 text-xs text-text_secondary">
          <div className="flex flex-col">
            <Tooltip content={t("tip_rsi")}>
              <span className="text-text_muted">RSI</span>
            </Tooltip>
            <span className="num text-text_primary">
              {plain ? humanizeRsi(indicators.rsi, dict) : indicators.rsi.toFixed(1)}
            </span>
          </div>
          <div className="flex flex-col">
            <Tooltip content={t("tip_ma")}>
              <span className="text-text_muted">MA20</span>
            </Tooltip>
            <span className="num text-text_primary">{indicators.ma20.toFixed(5)}</span>
          </div>
          <div className="flex flex-col">
            <Tooltip content={t("tip_ma")}>
              <span className="text-text_muted">MA50</span>
            </Tooltip>
            <span className="num text-text_primary">{indicators.ma50.toFixed(5)}</span>
          </div>
        </div>
      )}
    </div>
  );
}
