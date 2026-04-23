// Execute · Orderbook (L2) — single-symbol snapshot via REST.
// For live streaming use /execute/websocket (SSE fan-out of H0STASP0).
// Wired to GET /api/v1/execute/orderbook/{symbol} (FHKST01010200).
import { fetchEnvelope } from "@/lib/api";
import { EmptyState } from "@/components/shared/EmptyState";

export const dynamic = "force-dynamic";
export const revalidate = 10;

const DEFAULT_SYMBOL = "005930";

interface OrderbookData {
  levels: Array<{
    level: number;
    ask_price: string;
    ask_qty: string;
    bid_price: string;
    bid_qty: string;
  }>;
  total_ask_qty: string;
  total_bid_qty: string;
}

async function load(symbol: string): Promise<OrderbookData | null> {
  try {
    return await fetchEnvelope<OrderbookData>(
      `/api/v1/execute/orderbook/${symbol}`,
      { revalidate: 10 },
    );
  } catch {
    return null;
  }
}

const fmt = (v: string | undefined) =>
  !v ? "—" : isFinite(Number(v)) ? Number(v).toLocaleString() : v;

export default async function Page({
  searchParams,
}: {
  searchParams?: Promise<{ symbol?: string }>;
}) {
  const params = (await searchParams) ?? {};
  const symbol = (params.symbol ?? DEFAULT_SYMBOL).padStart(6, "0");
  const ob = await load(symbol);

  return (
    <div>
      <div className="breadcrumb">
        Execute <span className="sep">/</span>{" "}
        <span className="current">호가창 L2</span>
      </div>
      <div className="page-header">
        <div className="page-title-group">
          <h1>호가창 L2 · {symbol}</h1>
          <div className="page-meta">
            KIS REST 스냅샷 (FHKST01010200) · 10단계 · 실시간은 /execute/websocket
          </div>
        </div>
      </div>

      {!ob || !ob.levels?.length ? (
        <EmptyState
          variant="warn"
          title="호가 데이터를 불러올 수 없습니다"
          note="KIS OAuth 상태 또는 심볼을 확인하세요. ?symbol=000660 형태로 변경 가능."
          hint={`GET /api/v1/execute/orderbook/${symbol}`}
        />
      ) : (
        <div className="panel">
          <div className="panel-header">
            <h2>10단계 호가 · {symbol}</h2>
            <span className="muted">
              총매도 {fmt(ob.total_ask_qty)} · 총매수 {fmt(ob.total_bid_qty)}
            </span>
          </div>
          <div className="panel-body p0">
            <table className="mini">
              <thead>
                <tr>
                  <th style={{ textAlign: "right" }}>매도잔량</th>
                  <th style={{ textAlign: "right" }}>매도호가</th>
                  <th style={{ textAlign: "center" }}>Lv</th>
                  <th style={{ textAlign: "right" }}>매수호가</th>
                  <th style={{ textAlign: "right" }}>매수잔량</th>
                </tr>
              </thead>
              <tbody>
                {ob.levels.map((l) => (
                  <tr key={l.level}>
                    <td style={{ textAlign: "right", color: "var(--neg)" }}>{fmt(l.ask_qty)}</td>
                    <td style={{ textAlign: "right", color: "var(--neg)" }}>{fmt(l.ask_price)}</td>
                    <td style={{ textAlign: "center" }} className="mono">{l.level}</td>
                    <td style={{ textAlign: "right", color: "var(--pos)" }}>{fmt(l.bid_price)}</td>
                    <td style={{ textAlign: "right", color: "var(--pos)" }}>{fmt(l.bid_qty)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
