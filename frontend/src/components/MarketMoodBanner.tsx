import type { MoodResponse } from "../types";
import { useI18n } from "../i18n";
import { Tooltip } from "./Tooltip";

type Props = { mood: MoodResponse | null };

const LABEL_COLOR: Record<string, string> = {
  "Risk-On": "text-up",
  "Risk-Off": "text-down",
  Mixed: "text-warn",
};

export function MarketMoodBanner({ mood }: Props) {
  const { t } = useI18n();
  const label = mood?.label ?? "Mixed";
  const score = mood?.score ?? 50;
  const summary = mood?.summary ?? t("mood_warming");
  const localized =
    label === "Risk-On" ? t("mood_risk_on") : label === "Risk-Off" ? t("mood_risk_off") : t("mood_mixed");
  return (
    <div className="bg-surface border border-subtle rounded-lg p-5">
      <div className="flex items-baseline justify-between">
        <div>
          <Tooltip content={t("tip_mood")}>
            <span className="text-text_secondary text-xs">{t("mood_title")}</span>
          </Tooltip>
          <div className="flex items-baseline gap-3 mt-1">
            <span className={`text-2xl font-semibold ${LABEL_COLOR[label]}`}>{localized}</span>
            <span className="text-text_secondary text-sm">{summary}</span>
          </div>
        </div>
        <span className="num text-text_muted text-sm">{score}/100</span>
      </div>
      <div className="mt-3 relative h-2 rounded-full overflow-hidden bg-subtle">
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(90deg, rgba(240,104,104,0.7), rgba(245,177,76,0.5), rgba(46,211,167,0.7))",
          }}
        />
        <div className="absolute top-0 bottom-0 w-[2px] bg-text_primary" style={{ insetInlineStart: `${score}%` }} />
      </div>
    </div>
  );
}
