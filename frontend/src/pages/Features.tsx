import { useCallback, useEffect, useState } from "react";
import { features } from "../api/features";
import { useAuth } from "../auth/AuthContext";

type Section = { title: string; note?: string; children: React.ReactNode };

function Card({ title, note, children }: Section) {
  return (
    <section className="bg-surface border border-subtle rounded-lg p-5 space-y-3">
      <header>
        <div className="text-text_secondary text-xs uppercase tracking-wide">{title}</div>
        {note && <div className="text-text_muted text-xs mt-0.5">{note}</div>}
      </header>
      <div className="text-sm">{children}</div>
    </section>
  );
}

function labelColor(v: string): string {
  return (
    {
      HIGH: "text-down",
      MED: "text-warn",
      MEDIUM: "text-warn",
      LOW: "text-up",
      INFLOW: "text-up",
      OUTFLOW: "text-down",
      BALANCED: "text-text_secondary",
      ALIGNED: "text-up",
      RETAIL_EUPHORIA: "text-warn",
      RETAIL_CAPITULATION: "text-warn",
    } as Record<string, string>
  )[v] || "text-text_primary";
}

export function FeaturesPage() {
  const { token, user } = useAuth();
  const [narratives, setNarratives] = useState<any>(null);
  const [silence, setSilence] = useState<any>(null);
  const [consensus, setConsensus] = useState<any>(null);
  const [corr, setCorr] = useState<any>(null);
  const [calib, setCalib] = useState<any>(null);
  const [sources, setSources] = useState<any>(null);
  const [boringState, setBoringState] = useState<any>(null);
  const [contagion, setContagion] = useState<any>(null);
  const [personality, setPersonality] = useState<any>(null);
  const [timeMachine, setTimeMachine] = useState<any>(null);
  const [hoursBack, setHoursBack] = useState(1);
  const [digest, setDigest] = useState<any>(null);
  const [betStats, setBetStats] = useState<any>(null);
  const [betAsset, setBetAsset] = useState("EURUSD");
  const [betDir, setBetDir] = useState("UP");
  const [patternList, setPatternList] = useState<any[]>([]);
  const [patternName, setPatternName] = useState("");
  const [patternAsset, setPatternAsset] = useState("EURUSD");
  const [patternDir, setPatternDir] = useState("DOWN");
  const [patternMinProb, setPatternMinProb] = useState("0.6");

  const loadPublic = useCallback(async () => {
    const [n, si, co, cr, ca, so, bo, cg, pr] = await Promise.all([
      features.narratives(),
      features.silence(),
      features.consensus(),
      features.correlation(),
      features.calibration(),
      features.sources(),
      features.boring(),
      features.contagion(),
      features.personality("EURUSD"),
    ]);
    setNarratives(n);
    setSilence(si);
    setConsensus(co);
    setCorr(cr);
    setCalib(ca);
    setSources(so);
    setBoringState(bo);
    setContagion(cg);
    setPersonality(pr);
  }, []);

  useEffect(() => {
    loadPublic();
  }, [loadPublic]);

  useEffect(() => {
    if (!token) return;
    features.digest(token).then(setDigest).catch(() => {});
    features.bets.stats(token).then(setBetStats).catch(() => {});
    features.patterns.list(token).then(setPatternList).catch(() => {});
  }, [token]);

  const runTimeMachine = async () => {
    const iso = new Date(Date.now() - hoursBack * 3600 * 1000).toISOString();
    setTimeMachine(await features.timeMachine(iso));
  };

  const placeBet = async () => {
    if (!token) return;
    await features.bets.place(token, betAsset, betDir, 60);
    setBetStats(await features.bets.stats(token));
  };

  const createPattern = async () => {
    if (!token) return;
    const rules: any = {
      asset: patternAsset,
      direction: patternDir,
      min_probability: parseFloat(patternMinProb),
    };
    await features.patterns.create(token, patternName || "my pattern", rules);
    setPatternName("");
    setPatternList(await features.patterns.list(token));
  };

  const removePattern = async (id: number) => {
    if (!token) return;
    await features.patterns.remove(token, id);
    setPatternList(await features.patterns.list(token));
  };

  return (
    <main className="max-w-6xl mx-auto px-4 md:px-6 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Unique Features</h1>
        <p className="text-text_secondary text-sm">
          Fifteen capabilities that go beyond news + charts. Rule-based today, swappable with ML later.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="1. Time Machine" note="Replay the dashboard as it was in the past">
          <div className="flex items-center gap-2 mb-3">
            <input
              type="number"
              min={0}
              max={168}
              value={hoursBack}
              onChange={(e) => setHoursBack(parseInt(e.target.value || "1"))}
              className="w-20 bg-canvas border border-subtle rounded-md px-2 py-1 num"
            />
            <span className="text-text_muted text-xs">hours back</span>
            <button
              onClick={runTimeMachine}
              className="ml-auto bg-brand text-canvas rounded-md px-3 py-1 text-xs font-medium hover:brightness-110"
            >
              Replay
            </button>
          </div>
          {timeMachine && (
            <div className="space-y-1 text-xs">
              <div className="text-text_muted">as of {timeMachine.as_of}</div>
              {(timeMachine.signals || []).map((s: any) => (
                <div key={s.asset} className="flex justify-between">
                  <span>
                    {s.asset} <span className={labelColor(s.direction)}>{s.direction}</span>
                  </span>
                  <span className="num text-text_muted">{Math.round(Math.max(s.probabilities.up, s.probabilities.down, s.probabilities.neutral) * 100)}%</span>
                </div>
              ))}
              <div className="text-text_muted mt-2">news at that moment: {timeMachine.news?.length || 0}</div>
            </div>
          )}
        </Card>

        <Card title="2. Narrative Tracker" note="What the news is becoming about this week">
          <ul className="space-y-1">
            {(narratives?.items || []).map((n: any) => (
              <li key={n.term} className="flex justify-between text-xs">
                <span>
                  <span className="mr-2">{n.trend}</span>
                  <span className="text-text_primary">{n.term}</span>
                </span>
                <span className="num text-text_muted">
                  {n.current} vs {n.previous} · {n.ratio}x
                </span>
              </li>
            ))}
            {!narratives?.items?.length && <li className="text-text_muted text-xs">Not enough news history yet.</li>}
          </ul>
        </Card>

        <Card title="3. Silence Detector" note="News desks often know before they print">
          {silence && (
            <>
              <div className="flex items-baseline gap-2">
                <span className={`text-xl font-semibold ${silence.silent ? "text-warn" : "text-up"}`}>
                  {silence.silent ? "SILENT" : "NORMAL"}
                </span>
                <span className="text-text_muted text-xs num">
                  last 30m: {silence.recent} · baseline: {silence.baseline}
                </span>
              </div>
              <div className="text-xs text-text_secondary mt-1">{silence.note}</div>
            </>
          )}
        </Card>

        <Card title="4. Consensus Breaker" note="Released events with >1σ surprise">
          {!consensus?.items?.length && <div className="text-text_muted text-xs">No recent surprises.</div>}
          {(consensus?.items || []).map((c: any) => (
            <div key={c.kind + c.event_time} className="text-xs border-b border-subtle py-1.5">
              <div className="flex justify-between">
                <span className="text-text_primary">{c.kind} ({c.country})</span>
                <span className={`num ${c.surprise_sigma > 0 ? "text-up" : "text-down"}`}>{c.surprise_sigma}σ</span>
              </div>
              <div className="text-text_muted">{c.playbook}</div>
            </div>
          ))}
        </Card>

        <Card title="5. Correlation Break" note="Pairs that moved apart from their baseline">
          {(corr?.items || []).map((p: any) => (
            <div key={p.pair} className="flex justify-between text-xs py-0.5">
              <span>{p.pair}</span>
              <span className={`num ${p.break_flag ? "text-warn" : "text-text_muted"}`}>
                base {p.baseline_corr} → now {p.current_corr}
              </span>
            </div>
          ))}
          {!corr?.items?.length && <div className="text-text_muted text-xs">Need more OHLCV history.</div>}
        </Card>

        <Card title="6. Did I Miss Anything" note="Summary since your last visit">
          {!user && <div className="text-text_muted text-xs">Log in to see your personal digest.</div>}
          {digest && (
            <>
              <div className="text-xs text-text_muted">
                gap {digest.gap_minutes}m · {digest.high_impact_count} high-impact stories
              </div>
              <ul className="mt-2 space-y-1 text-xs">
                {(digest.news || []).slice(0, 4).map((n: any) => (
                  <li key={n.id} className="truncate">
                    <span className={labelColor(n.impact)}>{n.impact}</span>{" "}
                    <span className="text-text_primary">{n.title}</span>
                  </li>
                ))}
              </ul>
              {digest.direction_changes?.length > 0 && (
                <div className="mt-2 text-xs">
                  <div className="text-text_muted">direction changes:</div>
                  {digest.direction_changes.map((c: any) => (
                    <div key={c.asset}>
                      {c.asset}: {c.from} → <span className={labelColor(c.to)}>{c.to}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </Card>

        <Card title="7. Pattern Library" note="Custom rules across mood + signals">
          {!user && <div className="text-text_muted text-xs">Log in to save patterns.</div>}
          {user && (
            <>
              <div className="grid grid-cols-4 gap-2 mb-2">
                <input
                  value={patternName}
                  onChange={(e) => setPatternName(e.target.value)}
                  placeholder="name"
                  className="bg-canvas border border-subtle rounded-md px-2 py-1 text-xs col-span-2"
                />
                <select
                  value={patternAsset}
                  onChange={(e) => setPatternAsset(e.target.value)}
                  className="bg-canvas border border-subtle rounded-md px-2 py-1 text-xs"
                >
                  <option>EURUSD</option>
                  <option>BTCUSD</option>
                  <option>XAUUSD</option>
                </select>
                <select
                  value={patternDir}
                  onChange={(e) => setPatternDir(e.target.value)}
                  className="bg-canvas border border-subtle rounded-md px-2 py-1 text-xs"
                >
                  <option>UP</option>
                  <option>DOWN</option>
                  <option>NEUTRAL</option>
                </select>
                <input
                  value={patternMinProb}
                  onChange={(e) => setPatternMinProb(e.target.value)}
                  placeholder="min prob"
                  className="bg-canvas border border-subtle rounded-md px-2 py-1 text-xs num col-span-2"
                />
                <button
                  onClick={createPattern}
                  className="bg-brand text-canvas rounded-md px-2 py-1 text-xs font-medium col-span-2"
                >
                  Add pattern
                </button>
              </div>
              <ul className="space-y-1">
                {patternList.map((p: any) => (
                  <li key={p.id} className="flex justify-between text-xs border-t border-subtle pt-1">
                    <span>
                      <span className="text-text_primary">{p.name}</span>{" "}
                      <span className="text-text_muted">
                        {p.rules?.asset} {p.rules?.direction} ≥ {p.rules?.min_probability}
                      </span>
                    </span>
                    <button onClick={() => removePattern(p.id)} className="text-down">
                      remove
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </Card>

        <Card title="8. Confidence Calibration" note="Does 70% really mean 70%?">
          {calib && (
            <>
              <div className="text-text_muted text-xs">
                {calib.total} predictions over {calib.days}d · brier {calib.brier ?? "—"}
              </div>
              <table className="w-full text-xs mt-2">
                <thead className="text-text_muted">
                  <tr>
                    <th className="text-left font-normal">bin</th>
                    <th className="text-right font-normal">count</th>
                    <th className="text-right font-normal">hit rate</th>
                    <th className="text-right font-normal">ideal</th>
                  </tr>
                </thead>
                <tbody>
                  {(calib.curve || []).map((r: any) => (
                    <tr key={r.bin} className="border-t border-subtle">
                      <td>{r.bin}</td>
                      <td className="text-right num">{r.count}</td>
                      <td className="text-right num">{r.hit_rate ?? "—"}</td>
                      <td className="text-right num text-text_muted">{r.ideal}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </Card>

        <Card title="9. Retail vs Institutional" note="Sentiment split by source class">
          {sources && (
            <>
              <div className={`text-lg font-semibold ${labelColor(sources.flag)}`}>{sources.flag}</div>
              <div className="text-xs text-text_muted">divergence {sources.divergence}</div>
              <ul className="text-xs mt-2 space-y-0.5">
                {Object.entries(sources.groups).map(([k, v]: any) => (
                  <li key={k}>
                    <span className="capitalize">{k}</span>: {v.count} items · mean {v.mean_sentiment}
                  </li>
                ))}
              </ul>
            </>
          )}
        </Card>

        <Card title="10. Asset Personality" note="What this asset cares about">
          {personality && (
            <>
              <div className="text-text_primary font-semibold">{personality.symbol}</div>
              <div className="text-xs text-text_muted">{personality.static?.class}</div>
              <ul className="text-xs mt-1 space-y-0.5">
                <li>
                  <span className="text-text_muted">reactive: </span>
                  {(personality.static?.most_reactive_to || []).join(", ")}
                </li>
                <li>
                  <span className="text-text_muted">hours: </span>
                  {personality.static?.active_hours_utc}
                </li>
                <li>
                  <span className="text-text_muted">recent vol: </span>
                  <span className="num">{personality.dynamic?.recent_daily_vol_pct ?? "—"}%</span>
                </li>
              </ul>
            </>
          )}
        </Card>

        <Card title="11. Paper Bet" note="Track your own accuracy without risk">
          {!user && <div className="text-text_muted text-xs">Log in to place paper bets.</div>}
          {user && (
            <>
              <div className="flex items-center gap-2 mb-2">
                <select
                  value={betAsset}
                  onChange={(e) => setBetAsset(e.target.value)}
                  className="bg-canvas border border-subtle rounded-md px-2 py-1 text-xs"
                >
                  <option>EURUSD</option>
                  <option>BTCUSD</option>
                  <option>XAUUSD</option>
                </select>
                <select
                  value={betDir}
                  onChange={(e) => setBetDir(e.target.value)}
                  className="bg-canvas border border-subtle rounded-md px-2 py-1 text-xs"
                >
                  <option>UP</option>
                  <option>DOWN</option>
                  <option>NEUTRAL</option>
                </select>
                <button onClick={placeBet} className="bg-brand text-canvas rounded-md px-3 py-1 text-xs font-medium ml-auto">
                  Place 1h bet
                </button>
              </div>
              {betStats && (
                <div className="text-xs">
                  <div className="text-text_muted">
                    placed {betStats.placed} · resolved {betStats.resolved} · accuracy{" "}
                    <span className="num text-text_primary">
                      {betStats.accuracy === null ? "—" : `${Math.round(betStats.accuracy * 100)}%`}
                    </span>{" "}
                    · streak{" "}
                    <span className={betStats.streak > 0 ? "text-up" : betStats.streak < 0 ? "text-down" : ""}>
                      {betStats.streak}
                    </span>
                  </div>
                </div>
              )}
            </>
          )}
        </Card>

        <Card title="12. News-to-Chart Scrubbing" note="Backend ready: /features/news-markers">
          <div className="text-xs text-text_secondary">
            Markers endpoint provides ts + impact size for any chart. Chart-linked hover lives in the existing
            AssetCard; full scrubbing UI ships next.
          </div>
        </Card>

        <Card title="13. Soft Push" note="Subtle tab-badge hint">
          <SoftPush />
        </Card>

        <Card title="14. Contagion Map" note="If A moves hard, how often does B follow">
          {(contagion?.items || []).map((c: any) => (
            <div key={c.pair} className="flex justify-between text-xs py-0.5">
              <span>{c.pair}</span>
              <span className="num text-text_muted">
                same-sign rate{" "}
                <span className="text-text_primary">{(c.historical_same_sign_rate * 100).toFixed(0)}%</span>
              </span>
            </div>
          ))}
          {!contagion?.items?.length && <div className="text-text_muted text-xs">Need more history.</div>}
        </Card>

        <Card title="15. Boring Day Detector" note="The most profitable thing a retail trader can hear: don't trade today">
          {boringState && (
            <>
              <div className={`text-lg font-semibold ${boringState.boring ? "text-warn" : "text-up"}`}>
                {boringState.boring ? "BORING" : "ACTIVE"}
              </div>
              <div className="text-text_muted text-xs">
                score {boringState.score} · news {boringState.recent_news_4h} · vol{" "}
                {boringState.avg_realized_vol}
              </div>
              <div className="text-text_secondary text-xs mt-1">{boringState.note}</div>
            </>
          )}
        </Card>
      </div>
    </main>
  );
}

function SoftPush() {
  const [count, setCount] = useState(0);
  useEffect(() => {
    const tick = async () => {
      try {
        const d = await features.pushHint();
        setCount(d.new_high_impact);
        document.title =
          d.new_high_impact > 0 ? `(${d.new_high_impact}) MNI` : "Market News Intelligence";
      } catch {}
    };
    tick();
    const t = window.setInterval(tick, 30000);
    return () => window.clearInterval(t);
  }, []);
  return (
    <div className="text-xs text-text_secondary">
      Current tab badge count:{" "}
      <span className={count ? "text-warn num" : "text-text_muted num"}>{count}</span>
      <div className="text-text_muted mt-1">Tab title updates automatically on new high-impact news.</div>
    </div>
  );
}
