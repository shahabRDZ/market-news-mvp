import { useEffect, useState } from "react";
import { useI18n } from "../i18n";

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export function TodaysBriefCard() {
  const { t } = useI18n();
  const [sentences, setSentences] = useState<string[] | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch(`${BASE}/brief`);
        if (!r.ok) return;
        const d = await r.json();
        setSentences(d.sentences || []);
      } catch {}
    };
    load();
    const id = window.setInterval(load, 60000);
    return () => window.clearInterval(id);
  }, []);

  return (
    <div className="bg-raised border border-brand/30 rounded-lg p-5">
      <div className="text-xs text-brand uppercase tracking-wide mb-2">{t("brief_title")}</div>
      {sentences ? (
        <p className="text-text_primary text-base leading-relaxed">{sentences.join(" ")}</p>
      ) : (
        <p className="text-text_muted text-sm">{t("brief_loading")}</p>
      )}
    </div>
  );
}
