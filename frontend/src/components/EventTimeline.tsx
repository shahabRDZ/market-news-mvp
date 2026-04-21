import type { EconomicEvent } from "../types";

type Props = { events: EconomicEvent[] };

function humanDelta(iso: string): string {
  const ms = new Date(iso).getTime() - Date.now();
  const m = Math.round(ms / 60000);
  if (m <= 0) return "now";
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  const rem = m % 60;
  if (h < 24) return rem ? `${h}h ${rem}m` : `${h}h`;
  const d = Math.floor(h / 24);
  return `${d}d ${h % 24}h`;
}

const IMPORTANCE_COLOR: Record<number, string> = {
  3: "bg-warn",
  2: "bg-brand",
  1: "bg-neutral",
};

export function EventTimeline({ events }: Props) {
  if (events.length === 0) {
    return <div className="text-text_muted text-sm">No high-impact events in the next 48h.</div>;
  }
  return (
    <div className="space-y-3">
      {events.map((e) => {
        const delta = humanDelta(e.event_time);
        const soon = new Date(e.event_time).getTime() - Date.now() < 60 * 60 * 1000;
        return (
          <div key={e.id} className="flex items-center gap-3">
            <div className="flex flex-col items-center w-10">
              <span
                className={`w-2.5 h-2.5 rounded-full ${IMPORTANCE_COLOR[e.importance]} ${
                  soon ? "animate-pulse" : ""
                }`}
              />
              <span className="text-[10px] text-text_muted mt-1">{e.country}</span>
            </div>
            <div className="flex-1">
              <div className="text-sm text-text_primary">{e.kind}</div>
              <div className="text-[11px] text-text_muted">
                in {delta}
                {e.forecast !== null ? ` · fc ${e.forecast}` : ""}
                {e.previous !== null ? ` · prev ${e.previous}` : ""}
              </div>
            </div>
            <div className="flex flex-col items-end w-20">
              <div className="text-[10px] text-text_muted">pressure</div>
              <div className="num text-sm text-text_primary">{e.anticipation}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
