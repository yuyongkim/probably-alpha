"use client";

// TenantTable — list + create + rotate + disable.
// Admin token lives in localStorage (key: ky_admin_token) so this page can
// show mutating controls without a full auth system. GET always works.
import { useCallback, useEffect, useMemo, useState } from "react";
import type { TenantListResponse, TenantRow } from "@/types/admin";

const BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8300";
const TOKEN_KEY = "ky_admin_token";

type CreatedKey = { tenant_id: string; api_key: string } | null;

export function TenantTable() {
  const [tenants, setTenants] = useState<TenantRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [adminToken, setAdminToken] = useState<string>("");
  const [form, setForm] = useState({
    tenant_id: "",
    display_name: "",
    plan: "trial",
    rate_limit_per_min: 30,
  });
  const [createdKey, setCreatedKey] = useState<CreatedKey>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setAdminToken(window.localStorage.getItem(TOKEN_KEY) ?? "");
    }
  }, []);

  const headers = useMemo(() => {
    const h: Record<string, string> = { "Content-Type": "application/json" };
    if (adminToken) h["X-Admin-Token"] = adminToken;
    return h;
  }, [adminToken]);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${BASE}/api/v1/admin/tenants`, { headers, cache: "no-store" });
      const body = await res.json();
      if (!body.ok) throw new Error(body.error?.message ?? "fetch failed");
      setTenants((body.data as TenantListResponse).tenants);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [headers]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const persistToken = (value: string) => {
    setAdminToken(value);
    if (typeof window !== "undefined") {
      if (value) window.localStorage.setItem(TOKEN_KEY, value);
      else window.localStorage.removeItem(TOKEN_KEY);
    }
  };

  const handleCreate = async () => {
    if (!adminToken) {
      setError("admin token required for mutations");
      return;
    }
    setError(null);
    try {
      const res = await fetch(`${BASE}/api/v1/admin/tenants`, {
        method: "POST",
        headers,
        body: JSON.stringify(form),
      });
      const body = await res.json();
      if (!body.ok) throw new Error(body.error?.message ?? "create failed");
      setCreatedKey({ tenant_id: form.tenant_id, api_key: body.data.api_key });
      setForm({ ...form, tenant_id: "", display_name: "" });
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleRotate = async (tenantId: string) => {
    if (!adminToken) return;
    if (!confirm(`Rotate API key for '${tenantId}'? The old key will stop working.`)) return;
    try {
      const res = await fetch(`${BASE}/api/v1/admin/tenants/${tenantId}/rotate`, {
        method: "POST",
        headers,
      });
      const body = await res.json();
      if (!body.ok) throw new Error(body.error?.message ?? "rotate failed");
      setCreatedKey({ tenant_id: tenantId, api_key: body.data.api_key });
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleDisable = async (tenantId: string) => {
    if (!adminToken) return;
    if (!confirm(`Disable '${tenantId}'? All API calls from this tenant will be rejected.`)) return;
    try {
      const res = await fetch(`${BASE}/api/v1/admin/tenants/${tenantId}`, {
        method: "DELETE",
        headers,
      });
      const body = await res.json();
      if (!body.ok) throw new Error(body.error?.message ?? "disable failed");
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="space-y-4">
      <section
        className="rounded-md border p-3"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <div className="text-[10px] uppercase tracking-widest text-[color:var(--muted)] mb-2">
          Admin token
        </div>
        <div className="flex gap-2 items-center">
          <input
            type="password"
            className="flex-1 mono text-xs border px-2 py-1 rounded"
            style={{ background: "var(--bg)", borderColor: "var(--border)" }}
            value={adminToken}
            onChange={(e) => persistToken(e.target.value)}
            placeholder="KY_ADMIN_TOKEN (stored in localStorage)"
          />
          <span className="text-[10px] mono text-[color:var(--muted)]">
            {adminToken ? "admin" : "read-only"}
          </span>
        </div>
      </section>

      {createdKey ? (
        <section
          className="rounded-md border p-3"
          style={{ background: "var(--surface)", borderColor: "var(--pos)" }}
        >
          <div className="text-[10px] uppercase tracking-widest mb-1" style={{ color: "var(--pos)" }}>
            New API key — copy now (shown once)
          </div>
          <div className="mono text-xs break-all">{createdKey.api_key}</div>
          <div className="text-[10px] mono mt-1 text-[color:var(--muted)]">
            tenant: {createdKey.tenant_id}
          </div>
          <button
            className="mt-2 text-[11px] underline"
            onClick={() => setCreatedKey(null)}
          >
            dismiss
          </button>
        </section>
      ) : null}

      {error ? (
        <div
          className="rounded-md border px-3 py-2 text-xs"
          style={{ borderColor: "var(--neg)", color: "var(--neg)" }}
        >
          {error}
        </div>
      ) : null}

      <section>
        <h2 className="display text-base mb-2">
          Create tenant
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-2 items-end">
          <input
            className="mono text-xs border px-2 py-1 rounded"
            style={{ background: "var(--bg)", borderColor: "var(--border)" }}
            placeholder="tenant_id (e.g. acme)"
            value={form.tenant_id}
            onChange={(e) => setForm({ ...form, tenant_id: e.target.value })}
          />
          <input
            className="mono text-xs border px-2 py-1 rounded"
            style={{ background: "var(--bg)", borderColor: "var(--border)" }}
            placeholder="display name"
            value={form.display_name}
            onChange={(e) => setForm({ ...form, display_name: e.target.value })}
          />
          <select
            className="mono text-xs border px-2 py-1 rounded"
            style={{ background: "var(--bg)", borderColor: "var(--border)" }}
            value={form.plan}
            onChange={(e) => setForm({ ...form, plan: e.target.value })}
          >
            <option value="trial">trial</option>
            <option value="pro">pro</option>
            <option value="enterprise">enterprise</option>
          </select>
          <input
            type="number"
            className="mono text-xs border px-2 py-1 rounded"
            style={{ background: "var(--bg)", borderColor: "var(--border)" }}
            placeholder="req/min"
            value={form.rate_limit_per_min}
            onChange={(e) => setForm({ ...form, rate_limit_per_min: Number(e.target.value) || 30 })}
          />
          <button
            className="text-xs border px-3 py-1 rounded"
            style={{ background: "var(--accent)", color: "var(--bg)", borderColor: "var(--accent)" }}
            onClick={handleCreate}
            disabled={!adminToken || !form.tenant_id}
          >
            create
          </button>
        </div>
      </section>

      <section>
        <h2 className="display text-base mb-2">
          Tenants {loading ? "(loading…)" : `· ${tenants.length}`}
        </h2>
        <div
          className="rounded-md border overflow-hidden"
          style={{ borderColor: "var(--border)" }}
        >
          <table className="w-full text-xs">
            <thead style={{ background: "var(--surface)" }}>
              <tr className="text-left">
                <th className="px-3 py-2">tenant_id</th>
                <th className="px-3 py-2">display_name</th>
                <th className="px-3 py-2">plan</th>
                <th className="px-3 py-2 text-right">rate/min</th>
                <th className="px-3 py-2">status</th>
                <th className="px-3 py-2">created</th>
                <th className="px-3 py-2 text-right">actions</th>
              </tr>
            </thead>
            <tbody>
              {tenants.map((t) => (
                <tr key={t.tenant_id} className="border-t" style={{ borderColor: "var(--border)" }}>
                  <td className="px-3 py-2 mono">{t.tenant_id}</td>
                  <td className="px-3 py-2">{t.display_name}</td>
                  <td className="px-3 py-2 mono">{t.plan}</td>
                  <td className="px-3 py-2 text-right mono">{t.rate_limit_per_min}</td>
                  <td className="px-3 py-2" style={{ color: t.enabled ? "var(--pos)" : "var(--neg)" }}>
                    {t.enabled ? "enabled" : "disabled"}
                  </td>
                  <td className="px-3 py-2 mono text-[10px]">
                    {t.created_at ? t.created_at.slice(0, 19) : "—"}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {t.tenant_id === "self" ? (
                      <span className="text-[10px] text-[color:var(--muted)]">built-in</span>
                    ) : (
                      <div className="flex gap-2 justify-end">
                        <button
                          className="text-[11px] underline"
                          onClick={() => handleRotate(t.tenant_id)}
                          disabled={!adminToken}
                        >
                          rotate
                        </button>
                        {t.enabled ? (
                          <button
                            className="text-[11px] underline"
                            style={{ color: "var(--neg)" }}
                            onClick={() => handleDisable(t.tenant_id)}
                            disabled={!adminToken}
                          >
                            disable
                          </button>
                        ) : null}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
              {!loading && tenants.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-3 py-4 text-center text-[color:var(--muted)]">
                    no tenants
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
