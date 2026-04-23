"use client";

// UsageDashboard — per-tenant call count + avg latency + dummy pricing.
import { useCallback, useEffect, useMemo, useState } from "react";
import type { UsageResponse } from "@/types/admin";

const BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8300";
const TOKEN_KEY = "ky_admin_token";

export function UsageDashboard() {
  const [data, setData] = useState<UsageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sinceHours, setSinceHours] = useState(24);
  const [adminToken, setAdminToken] = useState("");

  useEffect(() => {
    if (typeof window !== "undefined") {
      setAdminToken(window.localStorage.getItem(TOKEN_KEY) ?? "");
    }
  }, []);

  const headers = useMemo(() => {
    const h: Record<string, string> = {};
    if (adminToken) h["X-Admin-Token"] = adminToken;
    return h;
  }, [adminToken]);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const res = await fetch(
        `${BASE}/api/v1/admin/usage?since_hours=${sinceHours}&limit=300`,
        { headers, cache: "no-store" },
      );
      const body = await res.json();
      if (!body.ok) throw new Error(body.error?.message ?? "fetch failed");
      setData(body.data as UsageResponse);
    } catch (err) {
      setError((err as Error).message);
    }
  }, [headers, sinceHours]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const totalCalls = data?.summary.reduce((s, r) => s + r.calls, 0) ?? 0;
  const totalFee = data?.summary.reduce((s, r) => s + r.monthly_fee_usd, 0) ?? 0;

  return (
    <div className="space-y-4">
      <div className="flex items-end gap-3">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-[color:var(--muted)] mb-1">
            window
          </div>
          <select
            className="mono text-xs border px-2 py-1 rounded"
            style={{ background: "var(--bg)", borderColor: "var(--border)" }}
            value={sinceHours}
            onChange={(e) => setSinceHours(Number(e.target.value))}
          >
            <option value={1}>last 1h</option>
            <option value={24}>last 24h</option>
            <option value={168}>last 7d</option>
            <option value={720}>last 30d</option>
          </select>
        </div>
        <div className="mono text-[10px] text-[color:var(--muted)]">
          since {data?.since ?? "—"}
        </div>
      </div>

      {error ? (
        <div
          className="rounded-md border px-3 py-2 text-xs"
          style={{ borderColor: "var(--neg)", color: "var(--neg)" }}
        >
          {error}
        </div>
      ) : null}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <Card label="Tenants with traffic" value={`${data?.summary.length ?? 0}`} />
        <Card label="Total calls" value={totalCalls.toLocaleString()} />
        <Card label="Monthly revenue (est.)" value={`$${totalFee.toFixed(0)}`} />
        <Card label="Events sampled" value={`${data?.events.length ?? 0}`} />
      </div>

      <section>
        <h2 className="display text-base mb-2">Per-tenant</h2>
        <div
          className="rounded-md border overflow-hidden"
          style={{ borderColor: "var(--border)" }}
        >
          <table className="w-full text-xs">
            <thead style={{ background: "var(--surface)" }}>
              <tr className="text-left">
                <th className="px-3 py-2">tenant_id</th>
                <th className="px-3 py-2">plan</th>
                <th className="px-3 py-2 text-right">calls</th>
                <th className="px-3 py-2 text-right">avg latency (ms)</th>
                <th className="px-3 py-2 text-right">monthly fee (USD)</th>
              </tr>
            </thead>
            <tbody>
              {data?.summary.map((r) => (
                <tr key={r.tenant_id} className="border-t" style={{ borderColor: "var(--border)" }}>
                  <td className="px-3 py-2 mono">{r.tenant_id}</td>
                  <td className="px-3 py-2 mono">{r.plan}</td>
                  <td className="px-3 py-2 text-right mono">{r.calls.toLocaleString()}</td>
                  <td className="px-3 py-2 text-right mono">{r.avg_latency_ms.toFixed(1)}</td>
                  <td className="px-3 py-2 text-right mono">${r.monthly_fee_usd.toFixed(0)}</td>
                </tr>
              ))}
              {data && data.summary.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-3 py-4 text-center text-[color:var(--muted)]">
                    no traffic yet
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="display text-base mb-2">Recent events</h2>
        <div
          className="rounded-md border overflow-hidden"
          style={{ borderColor: "var(--border)" }}
        >
          <table className="w-full text-xs">
            <thead style={{ background: "var(--surface)" }}>
              <tr className="text-left">
                <th className="px-3 py-2">ts</th>
                <th className="px-3 py-2">tenant</th>
                <th className="px-3 py-2">endpoint</th>
                <th className="px-3 py-2 text-right">latency</th>
                <th className="px-3 py-2 text-right">status</th>
              </tr>
            </thead>
            <tbody>
              {data?.events.slice(0, 200).map((e) => (
                <tr
                  key={e.id}
                  className="border-t"
                  style={{ borderColor: "var(--border)" }}
                >
                  <td className="px-3 py-2 mono text-[10px]">{e.ts.slice(0, 19)}</td>
                  <td className="px-3 py-2 mono">{e.tenant_id}</td>
                  <td className="px-3 py-2 mono">{e.endpoint}</td>
                  <td className="px-3 py-2 text-right mono">{e.latency_ms}</td>
                  <td
                    className="px-3 py-2 text-right mono"
                    style={{
                      color:
                        e.status_code >= 500
                          ? "var(--neg)"
                          : e.status_code >= 400
                          ? "var(--warn, #b08968)"
                          : "var(--pos)",
                    }}
                  >
                    {e.status_code}
                  </td>
                </tr>
              ))}
              {data && data.events.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-3 py-4 text-center text-[color:var(--muted)]">
                    no events yet
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

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div
      className="rounded-md border px-3 py-2"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
        {label}
      </div>
      <div className="display text-base mono">{value}</div>
    </div>
  );
}
