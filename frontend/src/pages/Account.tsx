import { useCallback, useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { api, useAuth } from "../auth/AuthContext";

type KeyOut = {
  id: number;
  name: string;
  prefix: string;
  created_at: string;
  last_used_at: string | null;
  revoked: boolean;
};

export function Account() {
  const { user, token, loading } = useAuth();
  const [keys, setKeys] = useState<KeyOut[]>([]);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [name, setName] = useState("default");
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const rows = await api<KeyOut[]>("/keys", token);
      setKeys(rows);
    } catch (e: any) {
      setErr(e?.message || "Failed to load keys");
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  if (!loading && !user) return <Navigate to="/login" replace />;

  const createKey = async () => {
    setErr(null);
    setNewKey(null);
    try {
      const data = await api<{ key: string; meta: KeyOut }>("/keys", token, {
        method: "POST",
        body: JSON.stringify({ name }),
      });
      setNewKey(data.key);
      setKeys((prev) => [data.meta, ...prev]);
    } catch (e: any) {
      setErr(e?.message || "Failed to create key");
    }
  };

  const revokeKey = async (id: number) => {
    await api(`/keys/${id}`, token, { method: "DELETE" });
    load();
  };

  return (
    <main className="max-w-3xl mx-auto px-4 md:px-6 py-12 space-y-10">
      <section>
        <h1 className="text-2xl font-semibold mb-1">Account</h1>
        <div className="text-text_secondary text-sm">{user?.email}</div>
      </section>

      <section className="bg-surface border border-subtle rounded-lg p-5">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-text_secondary text-xs mb-1">Current plan</div>
            <div className="text-xl font-semibold capitalize">{user?.plan}</div>
          </div>
          <div className="flex gap-2">
            {user?.has_subscription && (
              <button
                onClick={async () => {
                  try {
                    const { url } = await api<{ url: string }>("/billing/portal", token, { method: "POST" });
                    window.location.href = url;
                  } catch (e: any) {
                    setErr(e?.message || "Could not open billing portal");
                  }
                }}
                className="bg-raised text-text_primary rounded-md px-4 py-2 text-sm font-medium hover:brightness-110"
              >
                Manage subscription
              </button>
            )}
            <Link
              to="/pricing"
              className="bg-brand text-canvas rounded-md px-4 py-2 text-sm font-medium hover:brightness-110"
            >
              Change plan
            </Link>
          </div>
        </div>
      </section>

      <section className="bg-surface border border-subtle rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-text_secondary text-xs mb-1">API keys</div>
            <div className="text-lg font-semibold">Developer access</div>
          </div>
        </div>

        <div className="flex items-center gap-2 mb-4">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="key name (e.g. my-bot)"
            className="flex-1 bg-canvas border border-subtle rounded-md px-3 py-2 text-sm"
          />
          <button
            onClick={createKey}
            className="bg-brand text-canvas rounded-md px-4 py-2 text-sm font-medium hover:brightness-110"
          >
            Create key
          </button>
        </div>

        {err && <div className="text-down text-sm mb-3">{err}</div>}

        {newKey && (
          <div className="bg-raised border border-brand rounded-md p-3 mb-4">
            <div className="text-xs text-text_secondary mb-1">
              Copy this key now. It will not be shown again.
            </div>
            <div className="num text-sm break-all text-up">{newKey}</div>
          </div>
        )}

        <table className="w-full text-sm">
          <thead className="text-text_muted text-xs">
            <tr>
              <th className="text-left font-normal py-2">Name</th>
              <th className="text-left font-normal">Prefix</th>
              <th className="text-left font-normal">Created</th>
              <th className="text-left font-normal">Last used</th>
              <th />
            </tr>
          </thead>
          <tbody className="divide-y divide-subtle">
            {keys.length === 0 && (
              <tr>
                <td colSpan={5} className="text-text_muted text-center py-6">
                  No API keys yet.
                </td>
              </tr>
            )}
            {keys.map((k) => (
              <tr key={k.id} className={k.revoked ? "opacity-50" : ""}>
                <td className="py-2">{k.name}</td>
                <td className="num">{k.prefix}...</td>
                <td className="text-text_muted">{new Date(k.created_at).toLocaleDateString()}</td>
                <td className="text-text_muted">
                  {k.last_used_at ? new Date(k.last_used_at).toLocaleString() : "never"}
                </td>
                <td className="text-right">
                  {!k.revoked && (
                    <button
                      onClick={() => revokeKey(k.id)}
                      className="text-down hover:brightness-110 text-xs"
                    >
                      revoke
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="mt-4 text-xs text-text_muted">
          Send key via <span className="num">X-API-Key</span> header to any <span className="num">/v1/*</span>{" "}
          endpoint.
        </div>
      </section>
    </main>
  );
}
