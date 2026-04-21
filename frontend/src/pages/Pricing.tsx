import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, useAuth } from "../auth/AuthContext";

type Plan = {
  key: string;
  name: string;
  price_monthly: number;
  watchlist_limit: number;
  api_calls_per_day: number;
  ws_connections: number;
  history_days: number;
  realtime: boolean;
  llm_explanations: boolean;
};

const HIGHLIGHT = "premium";

export function Pricing() {
  const { token, user, refresh } = useAuth();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    api<{ plans: Plan[] }>("/billing/plans", null)
      .then((d) => setPlans(d.plans))
      .catch(() => setPlans([]));
  }, []);

  const select = async (planKey: string) => {
    if (!token) return;
    setBusy(planKey);
    try {
      await api<{ plan: string }>("/billing/select", token, {
        method: "POST",
        body: JSON.stringify({ plan: planKey }),
      });
      await refresh();
    } finally {
      setBusy(null);
    }
  };

  return (
    <main className="max-w-6xl mx-auto px-4 md:px-6 py-16">
      <div className="text-center mb-12">
        <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">Simple pricing</h1>
        <p className="text-text_secondary mt-2">Start free. Upgrade when the answer needs to be faster.</p>
      </div>
      <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-4">
        {plans.map((p) => {
          const isCurrent = user?.plan === p.key;
          const highlight = p.key === HIGHLIGHT;
          return (
            <div
              key={p.key}
              className={`bg-surface rounded-lg p-5 flex flex-col border ${
                highlight ? "border-brand" : "border-subtle"
              }`}
            >
              <div className="flex items-baseline justify-between">
                <div className="text-sm text-text_secondary">{p.name}</div>
                {highlight && <div className="text-[10px] text-brand uppercase tracking-wide">popular</div>}
              </div>
              <div className="mt-2">
                <span className="text-3xl font-semibold num">${p.price_monthly}</span>
                <span className="text-text_muted text-sm">/mo</span>
              </div>
              <ul className="text-sm space-y-1.5 mt-4 text-text_secondary flex-1">
                <li>{p.watchlist_limit} assets on watchlist</li>
                <li>{p.api_calls_per_day.toLocaleString()} API calls/day</li>
                <li>{p.ws_connections} realtime connections</li>
                <li>{p.history_days}d history</li>
                <li className={p.realtime ? "text-up" : "text-text_muted"}>
                  {p.realtime ? "Realtime updates" : "Delayed updates"}
                </li>
                <li className={p.llm_explanations ? "text-up" : "text-text_muted"}>
                  {p.llm_explanations ? "LLM explanations" : "Templated explanations"}
                </li>
              </ul>
              <div className="mt-5">
                {user ? (
                  isCurrent ? (
                    <div className="text-xs text-up text-center py-2">Current plan</div>
                  ) : (
                    <button
                      onClick={() => select(p.key)}
                      disabled={busy === p.key}
                      className={`w-full rounded-md py-2 text-sm font-medium ${
                        highlight ? "bg-brand text-canvas" : "bg-raised text-text_primary"
                      } hover:brightness-110 disabled:opacity-60`}
                    >
                      {busy === p.key ? "Switching..." : "Choose plan"}
                    </button>
                  )
                ) : (
                  <Link
                    to="/register"
                    className={`block text-center rounded-md py-2 text-sm font-medium ${
                      highlight ? "bg-brand text-canvas" : "bg-raised text-text_primary"
                    } hover:brightness-110`}
                  >
                    Get started
                  </Link>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <p className="text-text_muted text-xs text-center mt-10 max-w-2xl mx-auto">
        MVP mode: plan changes take effect immediately without a real payment. Stripe checkout is
        wired at the billing layer but not enabled for local development.
      </p>
    </main>
  );
}
