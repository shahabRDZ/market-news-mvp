import type { NewsItem } from "../types";
import { useI18n } from "../i18n";
import { Tooltip } from "./Tooltip";

const IMPACT_COLOR: Record<string, string> = {
  HIGH: "text-warn",
  MED: "text-brand",
  LOW: "text-text_muted",
};

function timeAgo(iso: string): string {
  const ms = Date.now() - new Date(iso).getTime();
  const m = Math.floor(ms / 60000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h`;
  return `${Math.floor(h / 24)}d`;
}

export function NewsList({ items }: { items: NewsItem[] }) {
  const { t } = useI18n();
  if (items.length === 0) {
    return <div className="text-text_muted text-sm">{t("news_waiting")}</div>;
  }
  const impactLabel = (imp: string) =>
    imp === "HIGH" ? t("news_impact_high") : imp === "MED" ? t("news_impact_med") : t("news_impact_low");
  return (
    <ul className="divide-y divide-subtle">
      {items.map((n) => {
        const tone =
          n.sentiment > 0.15 ? "text-up" : n.sentiment < -0.15 ? "text-down" : "text-text_secondary";
        return (
          <li key={n.id} className="py-3">
            <div className="flex items-center gap-2 text-xs">
              <Tooltip content={t("tip_impact")}>
                <span className={`${IMPACT_COLOR[n.impact] || ""} font-medium`}>{impactLabel(n.impact)}</span>
              </Tooltip>
              <span className="text-text_muted">{timeAgo(n.published_at)}</span>
              <span className="text-text_muted">·</span>
              <span className="text-text_muted">{n.source}</span>
              <span className={`ml-auto num ${tone}`}>{n.sentiment.toFixed(2)}</span>
            </div>
            <a
              href={n.url}
              target="_blank"
              rel="noreferrer"
              className="block mt-1 text-sm text-text_primary hover:text-brand"
            >
              {n.title}
            </a>
          </li>
        );
      })}
    </ul>
  );
}
