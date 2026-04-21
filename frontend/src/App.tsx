import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { NavBar } from "./components/NavBar";
import { Account } from "./pages/Account";
import { Dashboard } from "./pages/Dashboard";
import { Landing } from "./pages/Landing";
import { Login } from "./pages/Login";
import { Pricing } from "./pages/Pricing";
import { Register } from "./pages/Register";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen flex flex-col">
          <NavBar />
          <div className="flex-1">
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/pricing" element={<Pricing />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/account" element={<Account />} />
              <Route path="*" element={<Landing />} />
            </Routes>
          </div>
          <footer className="border-t border-subtle text-text_muted text-xs text-center py-4">
            © MNI. Informational only, not investment advice.
          </footer>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}
