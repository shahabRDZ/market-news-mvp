import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const TOKEN_KEY = "mni.token";

export type AuthUser = { id: number; email: string; plan: string };

type AuthContextShape = {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
};

const Ctx = createContext<AuthContextShape | null>(null);

async function authedJSON<T>(path: string, token: string | null, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (init?.headers) Object.assign(headers, init.headers);
  if (token) headers.Authorization = `Bearer ${token}`;
  const r = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!r.ok) throw new Error((await r.text()) || `HTTP ${r.status}`);
  return r.json() as Promise<T>;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const loadMe = useCallback(async (t: string | null) => {
    if (!t) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await authedJSON<AuthUser>("/auth/me", t);
      setUser(me);
    } catch {
      localStorage.removeItem(TOKEN_KEY);
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMe(token);
  }, [token, loadMe]);

  const handleAuth = (data: { token: string; user: AuthUser }) => {
    localStorage.setItem(TOKEN_KEY, data.token);
    setToken(data.token);
    setUser(data.user);
  };

  const login = async (email: string, password: string) => {
    const data = await authedJSON<{ token: string; user: AuthUser }>("/auth/login", null, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    handleAuth(data);
  };

  const register = async (email: string, password: string) => {
    const data = await authedJSON<{ token: string; user: AuthUser }>("/auth/register", null, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    handleAuth(data);
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  };

  const refresh = useCallback(() => loadMe(token), [loadMe, token]);

  return (
    <Ctx.Provider value={{ user, token, loading, login, register, logout, refresh }}>{children}</Ctx.Provider>
  );
}

export function useAuth() {
  const c = useContext(Ctx);
  if (!c) throw new Error("useAuth must be used inside AuthProvider");
  return c;
}

export async function api<T>(path: string, token: string | null, init?: RequestInit): Promise<T> {
  return authedJSON<T>(path, token, init);
}
