import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { en } from "./en";
import { fa } from "./fa";

export type Lang = "en" | "fa";
type Dict = Record<string, string>;

const DICTS: Record<Lang, Dict> = { en, fa };
const LANG_KEY = "mni.lang";
const PLAIN_KEY = "mni.plain";

type Ctx = {
  lang: Lang;
  setLang: (l: Lang) => void;
  plain: boolean;
  setPlain: (p: boolean) => void;
  t: (key: keyof typeof en, vars?: Record<string, string | number>) => string;
  dir: "ltr" | "rtl";
};

const I18nCtx = createContext<Ctx | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(
    () => (localStorage.getItem(LANG_KEY) as Lang) || "en",
  );
  const [plain, setPlainState] = useState<boolean>(
    () => localStorage.getItem(PLAIN_KEY) === "1",
  );

  const setLang = (l: Lang) => {
    localStorage.setItem(LANG_KEY, l);
    setLangState(l);
  };
  const setPlain = (p: boolean) => {
    localStorage.setItem(PLAIN_KEY, p ? "1" : "0");
    setPlainState(p);
  };

  const dir: "ltr" | "rtl" = lang === "fa" ? "rtl" : "ltr";

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = dir;
  }, [lang, dir]);

  const t = (key: keyof typeof en, vars?: Record<string, string | number>) => {
    const dict = DICTS[lang] || en;
    let str = (dict as Dict)[key] ?? (en as Dict)[key] ?? String(key);
    if (vars) {
      for (const [k, v] of Object.entries(vars)) str = str.replaceAll(`{${k}}`, String(v));
    }
    return str;
  };

  const value = useMemo<Ctx>(() => ({ lang, setLang, plain, setPlain, t, dir }), [lang, plain, dir]);
  return <I18nCtx.Provider value={value}>{children}</I18nCtx.Provider>;
}

export function useI18n() {
  const c = useContext(I18nCtx);
  if (!c) throw new Error("useI18n must be used inside I18nProvider");
  return c;
}
