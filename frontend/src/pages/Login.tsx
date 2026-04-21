import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      await login(email, password);
      nav("/dashboard");
    } catch (e: any) {
      setErr(e?.message || "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="max-w-sm mx-auto px-6 py-20">
      <h1 className="text-2xl font-semibold mb-6">Log in</h1>
      <form onSubmit={submit} className="space-y-4">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          className="w-full bg-surface border border-subtle rounded-md px-3 py-2 focus:outline-none focus:border-brand"
        />
        <input
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          className="w-full bg-surface border border-subtle rounded-md px-3 py-2 focus:outline-none focus:border-brand"
        />
        {err && <div className="text-down text-sm">{err}</div>}
        <button
          type="submit"
          disabled={busy}
          className="w-full bg-brand text-canvas rounded-md py-2 font-medium hover:brightness-110 disabled:opacity-60"
        >
          {busy ? "Signing in..." : "Log in"}
        </button>
      </form>
      <div className="text-text_muted text-sm mt-4">
        No account? <Link to="/register" className="text-brand">Register</Link>
      </div>
    </main>
  );
}
