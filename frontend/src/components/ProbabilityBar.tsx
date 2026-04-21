import type { Probabilities } from "../types";

type Props = { probs: Probabilities };

function Row({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-text_secondary w-14">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-subtle overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="num text-sm w-10 text-right">{pct}%</span>
    </div>
  );
}

export function ProbabilityBar({ probs }: Props) {
  return (
    <div className="space-y-2">
      <Row label="UP" value={probs.up} color="#2ED3A7" />
      <Row label="DOWN" value={probs.down} color="#F06868" />
      <Row label="NEUTRAL" value={probs.neutral} color="#6B7280" />
    </div>
  );
}
