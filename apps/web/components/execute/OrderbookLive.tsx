// OrderbookLive — real-time 10-level bid/ask ladder sourced from SSE.
"use client";

import { useEffect, useMemo, useState } from "react";

type Level = {
  level: number;
  ask_price?: string;
  ask_qty?: string;
  bid_price?: string;
  bid_qty?: string;
};

type OrderbookMsg = {
  type: "orderbook";
  symbol: string;
  data: {
    ts?: string;
    levels: Level[];
    total_ask_qty?: string;
    total_bid_qty?: string;
  };
};

type ConnState = "connecting" | "open" | "error" | "closed";

function apiBase() {
  return (
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    (typeof window !== "undefined" ? window.location.origin : "http://127.0.0.1:8300")
  );
}

function fmtNum(v: string | undefined): string {
  if (!v) return "—";
  const n = Number(v);
  if (!Number.isFinite(n)) return v;
  return n.toLocaleString("ko-KR");
}

export function OrderbookLive({ symbol }: { symbol: string }) {
  const [state, setState] = useState<ConnState>("connecting");
  const [levels, setLevels] = useState<Level[]>([]);
  const [ts, setTs] = useState<string | undefined>();
  const [totalAsk, setTotalAsk] = useState<string | undefined>();
  const [totalBid, setTotalBid] = useState<string | undefined>();
  const [msgCount, setMsgCount] = useState(0);

  useEffect(() => {
    const url = `${apiBase()}/api/v1/execute/stream/orderbook?symbol=${encodeURIComponent(symbol)}`;
    const es = new EventSource(url);

    es.addEventListener("ready", () => setState("open"));
    es.addEventListener("orderbook", (evt: MessageEvent) => {
      try {
        const msg = JSON.parse(evt.data) as OrderbookMsg;
        setLevels(msg.data.levels ?? []);
        setTs(msg.data.ts);
        setTotalAsk(msg.data.total_ask_qty);
        setTotalBid(msg.data.total_bid_qty);
        setMsgCount((c) => c + 1);
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

  const sorted = useMemo(() => {
    // Render asks top-down (10→1), bids 1→10 for a classic ladder look.
    const a = [...levels].sort((x, y) => y.level - x.level);
    return a;
  }, [levels]);

  const asks = sorted.filter((l) => l.ask_price && Number(l.ask_price) > 0);
  const bids = [...levels]
    .sort((x, y) => x.level - y.level)
    .filter((l) => l.bid_price && Number(l.bid_price) > 0);

  return (
    <div style={{ fontFamily: "var(--font-mono, monospace)", fontSize: 12 }}>
      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 8 }}>
        <strong>{symbol}</strong>
        <span style={{ color: state === "open" ? "var(--pos)" : state === "error" ? "var(--neg)" : "var(--muted)" }}>
          {state === "open" ? "LIVE" : state === "connecting" ? "…" : state === "error" ? "ERR" : "closed"}
        </span>
        <span style={{ color: "var(--muted)" }}>msgs: {msgCount}</span>
        {ts ? <span style={{ color: "var(--muted)" }}>ts: {ts}</span> : null}
      </div>
      <table className="mini" style={{ width: "100%" }}>
        <thead>
          <tr>
            <th className="num">Ask Qty</th>
            <th className="num">Ask</th>
            <th>Lvl</th>
            <th className="num">Bid</th>
            <th className="num">Bid Qty</th>
          </tr>
        </thead>
        <tbody>
          {asks.map((l) => (
            <tr key={`a${l.level}`}>
              <td className="num" style={{ color: "var(--neg)" }}>{fmtNum(l.ask_qty)}</td>
              <td className="num" style={{ color: "var(--neg)" }}>{fmtNum(l.ask_price)}</td>
              <td>{l.level}</td>
              <td className="num">—</td>
              <td className="num">—</td>
            </tr>
          ))}
          {bids.map((l) => (
            <tr key={`b${l.level}`}>
              <td className="num">—</td>
              <td className="num">—</td>
              <td>{l.level}</td>
              <td className="num" style={{ color: "var(--pos)" }}>{fmtNum(l.bid_price)}</td>
              <td className="num" style={{ color: "var(--pos)" }}>{fmtNum(l.bid_qty)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <td className="num" style={{ color: "var(--neg)" }}>{fmtNum(totalAsk)}</td>
            <td colSpan={3}>합계</td>
            <td className="num" style={{ color: "var(--pos)" }}>{fmtNum(totalBid)}</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
