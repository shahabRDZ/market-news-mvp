import { api } from "../auth/AuthContext";

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function getJSON<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json() as Promise<T>;
}

export const features = {
  timeMachine: (asOf: string) => getJSON<any>(`/features/timemachine?as_of=${encodeURIComponent(asOf)}`),
  narratives: () => getJSON<any>(`/features/narratives`),
  silence: () => getJSON<any>(`/features/silence`),
  consensus: () => getJSON<any>(`/features/consensus`),
  correlation: () => getJSON<any>(`/features/correlation`),
  digest: (token: string | null) => api<any>("/features/digest", token),
  patterns: {
    list: (token: string | null) => api<any>("/features/patterns", token),
    create: (token: string | null, name: string, rules: any) =>
      api<any>("/features/patterns", token, { method: "POST", body: JSON.stringify({ name, rules }) }),
    remove: (token: string | null, id: number) =>
      api<any>(`/features/patterns/${id}`, token, { method: "DELETE" }),
    matches: (token: string | null, moodLabel: string) =>
      api<any>(`/features/patterns/matches?mood_label=${encodeURIComponent(moodLabel)}`, token),
  },
  calibration: (horizon = 60, days = 30) => getJSON<any>(`/features/calibration?horizon=${horizon}&days=${days}`),
  sources: (hours = 24) => getJSON<any>(`/features/sources?hours=${hours}`),
  personality: (symbol: string) => getJSON<any>(`/features/personality/${symbol}`),
  bets: {
    place: (token: string | null, asset: string, direction: string, horizonMinutes: number) =>
      api<any>("/features/bets", token, {
        method: "POST",
        body: JSON.stringify({ asset, direction, horizon_minutes: horizonMinutes }),
      }),
    stats: (token: string | null) => api<any>("/features/bets", token),
  },
  contagion: () => getJSON<any>(`/features/contagion`),
  boring: () => getJSON<any>(`/features/boring`),
  newsMarkers: (asset: string, hours = 24) => getJSON<any>(`/features/news-markers?asset=${asset}&hours=${hours}`),
  pushHint: () => getJSON<any>(`/features/push-hint`),
};
