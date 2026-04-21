import { useEffect, useState } from "react";
import { fetchIntel, fetchReplay } from "../api/client";
import type { IntelPayload } from "../types";

type Props = { asset: string };

const LEVEL_COLOR: Record<string, string> = {
  HIGH: "text-down",
  MED: "text-warn",
  MEDIUM: "text-warn",
  LOW: "text-up",
};

const FLOW_COLOR: Record<string, string> = {
  INFLOW: "text-up",
  OUTFLOW: "text-down",
  BALANCED: "text-text_secondary",
};

function Bar({ value, color = "#6D8CFF" }: { value: number; color?: string }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className="h-1.5 rounded-full bg-subtle overflow-hidden">
      <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}

export function AdvancedIntelPanel({ asset }: Props) {
  const [intel, setIntel] = useState<IntelPayload | null>(null);
  const [replayOpen, setReplayOpen] = useState(false);
  const [replay, setReplay] = useState<Awaited<ReturnType<typeof fetchReplay>> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      fetchIntel(asset)
        .then((d) => !cancelled && setIntel(d))
        .catch(() => {});
    };
    load();
    const t = window.setInterval(load, 20000);
    return () => {
      cancelled = true;
      window.clearInterval(t);
    };
  }, [asset]);

  const openReplay = async () => {
    setReplayOpen(true);
    if (!replay) {
      setLoading(true);
      try {
        setReplay(await fetchReplay(asset));
      } finally {
        setLoading(false);
      }
    }
  };

  if (!intel) {
    return (
      <div className="bg-surface border border-subtle rounded-lg p-5 text-text_muted text-sm">
        Loading market intelligence for {asset}...
      </div>
    );
  }

  return (
    <div className="bg-surface border border-subtle rounded-lg p-5 space-y-5">
      <div className="flex items-baseline justify-between">
        <div>
          <div className="text-text_secondary text-xs">Advanced Market Intel</div>
          <div className="flex items-baseline gap-2">
            <span className="text-lg font-semibold">{asset}</span>
            <span className={`text-xs ${LEVEL_COLOR[intel.market_state]}`}>{intel.market_state}</span>
          </div>
        </div>
        <button
          onClick={openReplay}
          className="text-xs text-brand hover:brightness-110 border border-subtle rounded-md px-2 py-1"
        >
          Replay similar news
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Tile title="Pre-News Stress" highlight={intel.stress.level}>
          <div className="flex items-baseline gap-2">
            <span className={`text-xl font-semibold ${LEVEL_COLOR[intel.stress.level]}`}>
              {intel.stress.level}
            </span>
            <span className="num text-text_muted text-xs">{intel.stress.score}/100</span>
          </div>
          <Bar value={intel.stress.score} color="#F5B14C" />
          <div className="text-text_secondary text-xs">{intel.stress.reason}</div>
        </Tile>

        <Tile title="Pre-News Countdown">
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-semibold num">{intel.pre_news.minutes_to_event || 0}m</span>
            <span className="text-text_muted text-xs">{intel.pre_news.event_kind || "no event"}</span>
          </div>
          <Bar value={intel.pre_news.pressure} color="#6D8CFF" />
          <div className="text-xs">
            <span className="text-text_secondary">fake-move risk </span>
            <span className={LEVEL_COLOR[intel.pre_news.fake_move_risk]}>
              {intel.pre_news.fake_move_risk}
            </span>
          </div>
        </Tile>

        <Tile title="Smart Money Flow">
          <div className="flex items-baseline gap-2">
            <span className={`text-xl font-semibold ${FLOW_COLOR[intel.smart_money_flow.flow]}`}>
              {intel.smart_money_flow.flow}
            </span>
            <span className="num text-text_muted text-xs">{intel.smart_money_flow.score}</span>
          </div>
          <div className="text-xs text-text_secondary">
            trap probability <span className="num">{intel.smart_money_flow.trap_probability}</span>
          </div>
          <ul className="text-xs text-text_muted space-y-0.5">
            {intel.smart_money_flow.notes.slice(0, 2).map((n) => (
              <li key={n}>· {n}</li>
            ))}
          </ul>
        </Tile>

        <Tile title="Contradiction">
          <div className="flex items-baseline gap-2">
            <span
              className={`text-xl font-semibold ${
                intel.contradiction.flagged ? "text-warn" : "text-up"
              }`}
            >
              {intel.contradiction.flagged ? "OPPOSITE" : intel.contradiction.direction.toUpperCase()}
            </span>
          </div>
          <div className="text-xs text-text_secondary">{intel.contradiction.note}</div>
          <div className="text-[10px] text-text_muted num">
            news {intel.contradiction.news_bias.toFixed(2)} · price
            {" "}
            {(intel.contradiction.price_return * 100).toFixed(2)}%
          </div>
        </Tile>
      </div>

      <div>
        <div className="text-text_secondary text-xs mb-2">Liquidity Zones</div>
        {intel.liquidity_zones.length === 0 && (
          <div className="text-text_muted text-xs">No clear zones detected.</div>
        )}
        <ul className="space-y-1">
          {intel.liquidity_zones.map((z) => (
            <li key={`${z.level}-${z.side}`} className="flex items-center justify-between text-xs">
              <span className={z.side === "above" ? "text-up" : "text-down"}>
                {z.side === "above" ? "↑" : "↓"} {z.level}
              </span>
              <span className="text-text_muted num">
                {z.touches}× · {z.distance_pct.toFixed(2)}%
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="text-xs text-text_secondary italic">"{intel.explanation}"</div>

      {replayOpen && (
        <div className="border-t border-subtle pt-4">
          <div className="flex items-center justify-between mb-2">
            <div className="text-text_secondary text-xs">News Reaction Replay</div>
            <button onClick={() => setReplayOpen(false)} className="text-text_muted text-xs">
              close
            </button>
          </div>
          {loading && <div className="text-text_muted text-xs">Loading...</div>}
          {!loading && replay && replay.target && (
            <>
              <div className="text-sm text-text_primary mb-2">target: {replay.target.title}</div>
              {replay.outcomes.length === 0 ? (
                <div className="text-text_muted text-xs">No similar past events yet.</div>
              ) : (
                <table className="w-full text-xs">
                  <thead className="text-text_muted">
                    <tr>
                      <th className="text-left font-normal py-1">Similar</th>
                      <th className="text-right font-normal">sim</th>
                      <th className="text-right font-normal">15m</th>
                      <th className="text-right font-normal">1h</th>
                      <th className="text-right font-normal">4h</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-subtle">
                    {replay.outcomes.map((o) => (
                      <tr key={o.news_id}>
                        <td className="py-1 pr-2">{o.title.slice(0, 56)}...</td>
                        <td className="num text-right">{o.similarity}</td>
                        <td className={`num text-right ${(o.ret_15m || 0) > 0 ? "text-up" : (o.ret_15m || 0) < 0 ? "text-down" : ""}`}>
                          {o.ret_15m === null ? "—" : `${(o.ret_15m * 100).toFixed(2)}%`}
                        </td>
                        <td className={`num text-right ${(o.ret_1h || 0) > 0 ? "text-up" : (o.ret_1h || 0) < 0 ? "text-down" : ""}`}>
                          {o.ret_1h === null ? "—" : `${(o.ret_1h * 100).toFixed(2)}%`}
                        </td>
                        <td className={`num text-right ${(o.ret_4h || 0) > 0 ? "text-up" : (o.ret_4h || 0) < 0 ? "text-down" : ""}`}>
                          {o.ret_4h === null ? "—" : `${(o.ret_4h * 100).toFixed(2)}%`}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

function Tile({
  title,
  children,
  highlight,
}: {
  title: string;
  children: React.ReactNode;
  highlight?: string;
}) {
  return (
    <div className="bg-raised border border-subtle rounded-md p-3 space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="text-text_muted text-[10px] uppercase tracking-wide">{title}</div>
        {highlight && <div className={`text-[10px] ${LEVEL_COLOR[highlight]}`}>{highlight}</div>}
      </div>
      {children}
    </div>
  );
}
