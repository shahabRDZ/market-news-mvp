import { Link } from "react-router-dom";

export function Landing() {
  return (
    <main className="max-w-6xl mx-auto px-4 md:px-6 py-16 md:py-24">
      <section className="text-center space-y-6">
        <div className="inline-flex items-center gap-2 text-xs text-text_secondary border border-subtle rounded-full px-3 py-1">
          <span className="w-1.5 h-1.5 rounded-full bg-up animate-pulse" />
          Real-time market intelligence, not trading signals
        </div>
        <h1 className="text-4xl md:text-6xl font-semibold tracking-tight">
          The market, <span className="text-brand">answered</span> in 5 seconds.
        </h1>
        <p className="text-text_secondary max-w-2xl mx-auto text-lg">
          MNI reads the news, watches the charts, tracks the calendar, and tells you what is
          happening, why, and what is probably next. Calibrated probabilities, not hype.
        </p>
        <div className="flex items-center justify-center gap-3 pt-2">
          <Link
            to="/register"
            className="bg-brand text-canvas font-medium rounded-md px-5 py-2.5 hover:brightness-110"
          >
            Start free
          </Link>
          <Link to="/dashboard" className="text-text_secondary hover:text-text_primary px-5 py-2.5">
            See live demo
          </Link>
        </div>
      </section>

      <section className="grid md:grid-cols-3 gap-5 mt-20">
        {[
          { t: "Market Mood", d: "One-line synthesis across FX, metals, crypto. No dashboards to read." },
          { t: "Direction Probability", d: "Calibrated UP / DOWN / NEUTRAL with the features that drove it." },
          { t: "Coming Soon Impact", d: "Anticipation pressure for CPI, FOMC, NFP, rate decisions." },
        ].map((f) => (
          <div key={f.t} className="bg-surface border border-subtle rounded-lg p-6">
            <div className="text-sm text-text_muted mb-1">0{["1", "2", "3"][Math.floor(Math.random() * 3)]}</div>
            <div className="text-lg font-semibold">{f.t}</div>
            <div className="text-text_secondary text-sm mt-2">{f.d}</div>
          </div>
        ))}
      </section>

      <section className="mt-24 text-center">
        <div className="text-text_muted text-sm">Built for retail traders, newsletters, prop firms, and fintech builders.</div>
      </section>
    </main>
  );
}
