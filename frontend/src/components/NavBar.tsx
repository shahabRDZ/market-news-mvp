import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useI18n } from "../i18n";

export function NavBar() {
  const { user, logout } = useAuth();
  const { t, lang, setLang, plain, setPlain } = useI18n();

  return (
    <header className="border-b border-subtle bg-canvas/80 backdrop-blur sticky top-0 z-10">
      <div className="max-w-6xl mx-auto flex items-center justify-between gap-4 px-4 md:px-6 h-14">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-brand" />
          <span className="font-semibold tracking-tight">MNI</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm text-text_secondary">
          <NavLink to="/dashboard" className={({ isActive }) => (isActive ? "text-text_primary" : "hover:text-text_primary")}>
            {t("nav_dashboard")}
          </NavLink>
          <NavLink to="/features" className={({ isActive }) => (isActive ? "text-text_primary" : "hover:text-text_primary")}>
            {t("nav_features")}
          </NavLink>
          <NavLink to="/pricing" className={({ isActive }) => (isActive ? "text-text_primary" : "hover:text-text_primary")}>
            {t("nav_pricing")}
          </NavLink>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="hover:text-text_primary">
            {t("nav_api")}
          </a>

          <label className="flex items-center gap-1.5 text-xs text-text_muted cursor-pointer select-none">
            <input
              type="checkbox"
              checked={plain}
              onChange={(e) => setPlain(e.target.checked)}
              className="accent-brand"
            />
            {t("label_plain")}
          </label>

          <select
            value={lang}
            onChange={(e) => setLang(e.target.value as "en" | "fa")}
            className="bg-surface border border-subtle text-xs rounded-md px-2 py-1 text-text_primary"
            aria-label={t("label_language")}
          >
            <option value="en">EN</option>
            <option value="fa">فا</option>
          </select>

          {user ? (
            <>
              <NavLink to="/account" className={({ isActive }) => (isActive ? "text-text_primary" : "hover:text-text_primary")}>
                {t("nav_account")}
              </NavLink>
              <button onClick={logout} className="text-text_muted hover:text-text_primary">
                {t("nav_logout")}
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className="hover:text-text_primary">{t("nav_login")}</NavLink>
              <NavLink
                to="/register"
                className="bg-brand text-canvas font-medium rounded-md px-3 py-1.5 hover:brightness-110"
              >
                {t("nav_register")}
              </NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
