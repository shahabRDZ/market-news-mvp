import { en } from "./en";
import { fa } from "./fa";

type Dict = typeof en;

export function humanizeRsi(rsi: number, d: Dict): string {
  if (rsi >= 70) return d.plain_overbought;
  if (rsi <= 30) return d.plain_oversold;
  return d.plain_balanced_rsi;
}

export function humanizeTrend(
  trend: "up" | "down" | "flat" | string,
  d: Dict,
): string {
  if (trend === "up") return d.plain_uptrend;
  if (trend === "down") return d.plain_downtrend;
  return d.plain_flat;
}

export function humanizeSentiment(s: number, d: Dict): string {
  if (s >= 0.5) return d.plain_sentiment_very_pos;
  if (s >= 0.15) return d.plain_sentiment_pos;
  if (s <= -0.5) return d.plain_sentiment_very_neg;
  if (s <= -0.15) return d.plain_sentiment_neg;
  return d.plain_sentiment_neu;
}

export function humanizeDirection(dir: string, d: Dict): string {
  if (dir === "UP") return d.plain_leaning_up;
  if (dir === "DOWN") return d.plain_leaning_down;
  return d.plain_unclear;
}

export { en as EN, fa as FA };
