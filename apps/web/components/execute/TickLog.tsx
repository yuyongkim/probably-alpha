// TickLog — rolling log of recent tick events + live 체결강도 readout.
"use client";

import { useEffect, useMemo, useState } from "react";
import { apiBase } from "@/lib/apiBase";

type Tick = {
  ts?: string;
  price?: string;
  change?: string;
  change_sign?: string;
  change_pct?: string;
  qty?: string;
  strength?: string;
  buy_ratio?: string;
  direction?: string;
};

type TickMsg = { type: "tick"; symbol: string; data: Tick };

type ConnState = "connecting" | "open" | "error" | "closed";

const MAX_ROWS = 15;

function fmtNum(v: string | undefined): string {
  if (!v) return "—";
  const n = Number(v);
  if (!Number.isFinite(n)) return v;
  return n.toLocaleString("ko-KR");
}

function formatTs(v: string | undefined): string {
  if (!v || v.length < 6) return v ?? "—";
  // HHMMSS → HH:MM:SS
  return `${v.slice(0, 2)}:${v.slice(2, 4)}:${v.slice(4, 6)}`;
}

function signTone(sign?: string): string {
  if (!sign) return "var(--muted)";
  // KIS sign codes: 1 상한 · 2 상승 · 3 보합 · 4 하한 · 5 하락
  if (sign === "1" || sign === "2") return "var(--pos)";
  if (sign === "4" || sign === "5") return "var(--neg)";
  return "var(--muted)";
}

function directionLabel(d?: string): string {
  if (d === "1") return "매수";
  if (d === "3") return "매도";
  if (d === "5") return "장전";
  return d ?? "—";
}

export function TickLog({ symbol }: { symbol: string }) {
  const [state, setState] = useState<ConnState>("connecting");
  const [rows, setRows] = useState<Tick[]>([]);
  const [latest, setLatest] = useState<Tick | null>(null);
  const [count, setCount] = useState(0);

  useEffect(() => {
    const url = `${apiBase()}/api/v1/execute/stream/ticks?symbol=${encodeURIComponent(symbol)}`;
    const es = new EventSource(url);
    es.addEventListener("ready", () => setState("open"));
    es.addEventListener("tick", (evt: MessageEvent) => {
      try {
        const msg = JSON.parse(evt.data) as TickMsg;
        setLatest(msg.data);
        setRows((prev) => {
          const next = [msg.data, ...prev];
          return next.slice(0, MAX_ROWS);
        });
        setCount((c) => c + 1);
      } catch {
        /* ignore */
      }
    });
    es.addEventListener("error", () => setState("error"));
    es.onerror = () => setState("error");

    return () => {
      es.close();
      setState("closed");
    };
  }, [symbol]);

  const strength = useMemo(() => {
    // Derive client-side 체결강도 as buy_ratio (already computed by KIS);
    // fall back to KIS `cttr` if buy_ratio is empty.
    return latest?.strength ?? latest?.buy_ratio ?? null;
  }, [latest]);

  return (
    <div style={{ fontFamily: "var(--font-mono, monospace)", fontSize: 12 }}>
      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 8 }}>
        <strong>{symbol} · 체결</strong>
        <span style={{ color: state === "open" ? "var(--pos)" : state === "error" ? "var(--neg)" : "var(--muted)" }}>
          {state === "open" ? "LIVE" : state === "connecting" ? "…" : state === "error" ? "ERR" : "closed"}
        </span>
        <span style={{ color: "var(--muted)" }}>ticks: {count}</span>
        {strength ? (
          <span>
            체결강도:&nbsp;
            <strong style={{ color: Number(strength) >= 100 ? "var(--pos)" : "var(--neg)" }}>
              {strength}
            </strong>
          </span>
        ) : null}
      </div>
      <table className="mini" style={{ width: "100%" }}>
        <thead>
          <tr>
            <th>Time</th>
            <th className="num">Price</th>
            <th className="num">Chg%</th>
            <th className="num">Qty</th>
            <th>Dir</th>
            <th className="num">Strg</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={6} style={{ color: "var(--muted)" }}>
                (waiting for ticks — 장중에만 수신됩니다)
              </td>
            </tr>
          ) : (
            rows.map((t, i) => (
              <tr key={`${t.ts}-${i}`}>
                <td>{formatTs(t.ts)}</td>
                <td className="num" style={{ color: signTone(t.change_sign) }}>{fmtNum(t.price)}</td>
                <td className="num" style={{ color: signTone(t.change_sign) }}>{t.change_pct ?? "—"}</td>
                <td className="num">{fmtNum(t.qty)}</td>
                <td>{directionLabel(t.direction)}</td>
                <td className="num">{t.strength ?? "—"}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
