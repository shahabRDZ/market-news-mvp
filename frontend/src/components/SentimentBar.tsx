type Props = { value: number };

export function SentimentBar({ value }: Props) {
  const clamped = Math.max(-1, Math.min(1, value));
  const pct = ((clamped + 1) / 2) * 100;
  return (
    <div>
      <div className="flex items-center justify-between text-xs text-text_secondary mb-1">
        <span>Sentiment</span>
        <span className="num">{clamped.toFixed(2)}</span>
      </div>
      <div className="relative h-2 rounded-full overflow-hidden bg-subtle">
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(90deg, rgba(240,104,104,0.6), rgba(107,114,128,0.4), rgba(46,211,167,0.6))",
          }}
        />
        <div
          className="absolute top-0 bottom-0 w-[2px] bg-text_primary"
          style={{ left: `${pct}%` }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-text_muted mt-1">
        <span>-1</span>
        <span>0</span>
        <span>+1</span>
      </div>
    </div>
  );
}
