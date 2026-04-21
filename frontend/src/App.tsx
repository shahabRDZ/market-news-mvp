import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { I18nProvider, useI18n } from "./i18n";
import { NavBar } from "./components/NavBar";
import { Account } from "./pages/Account";
import { Dashboard } from "./pages/Dashboard";
import { FeaturesPage } from "./pages/Features";
import { Landing } from "./pages/Landing";
import { Login } from "./pages/Login";
import { Pricing } from "./pages/Pricing";
import { Register } from "./pages/Register";

function Shell() {
  const { t, dir } = useI18n();
  return (
    <div className="min-h-screen flex flex-col" dir={dir}>
      <NavBar />
      <div className="flex-1">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/features" element={<FeaturesPage />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/account" element={<Account />} />
          <Route path="*" element={<Landing />} />
        </Routes>
      </div>
      <footer className="border-t border-subtle text-text_muted text-xs text-center py-4">
        {t("disclaimer")}
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <I18nProvider>
      <AuthProvider>
        <BrowserRouter>
          <Shell />
        </BrowserRouter>
      </AuthProvider>
    </I18nProvider>
  );
}
