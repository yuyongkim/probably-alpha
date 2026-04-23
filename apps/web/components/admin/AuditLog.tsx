"use client";

// AuditLog — table of sensitive-action events. Admins see everyone; otherwise
// scoped to the 'self' tenant.
import { useCallback, useEffect, useMemo, useState } from "react";
import type { AuditResponse } from "@/types/admin";

const BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8300";
const TOKEN_KEY = "ky_admin_token";

export function AuditLog() {
  const [data, setData] = useState<AuditResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
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
      const res = await fetch(`${BASE}/api/v1/admin/audit?limit=500`, {
        headers,
        cache: "no-store",
      });
      const body = await res.json();
      if (!body.ok) throw new Error(body.error?.message ?? "fetch failed");
      setData(body.data as AuditResponse);
    } catch (err) {
      setError((err as Error).message);
    }
  }, [headers]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <div className="space-y-3">
      <div className="text-[10px] mono text-[color:var(--muted)]">
        {data ? `${data.count} events` : "loading…"}
        {adminToken ? " · admin view" : " · self-scope"}
      </div>
      {error ? (
        <div
          className="rounded-md border px-3 py-2 text-xs"
          style={{ borderColor: "var(--neg)", color: "var(--neg)" }}
        >
          {error}
        </div>
      ) : null}
      <div
        className="rounded-md border overflow-hidden"
        style={{ borderColor: "var(--border)" }}
      >
        <table className="w-full text-xs">
          <thead style={{ background: "var(--surface)" }}>
            <tr className="text-left">
              <th className="px-3 py-2">ts</th>
              <th className="px-3 py-2">tenant</th>
              <th className="px-3 py-2">action</th>
              <th className="px-3 py-2">detail</th>
            </tr>
          </thead>
          <tbody>
            {data?.events.map((e) => (
              <tr key={e.id} className="border-t" style={{ borderColor: "var(--border)" }}>
                <td className="px-3 py-2 mono text-[10px]">{e.ts.slice(0, 19)}</td>
                <td className="px-3 py-2 mono">{e.tenant_id}</td>
                <td className="px-3 py-2 mono">{e.action}</td>
                <td className="px-3 py-2 mono text-[10px] whitespace-pre-wrap break-all">
                  {e.detail ?? "—"}
                </td>
              </tr>
            ))}
            {data && data.events.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-3 py-4 text-center text-[color:var(--muted)]">
                  no audit events
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
