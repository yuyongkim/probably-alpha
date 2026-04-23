// Execute · KR Stock — live KIS stock_price + fluctuation Top-N (실데이터).
import { DensePage } from "@/components/shared/DensePage";
import { SummaryCards } from "@/components/shared/SummaryCards";
import { EmptyState } from "@/components/shared/EmptyState";
import { fetchEnvelope } from "@/lib/api";

export const revalidate = 60;

interface QuoteData {
  price: string;
  change: string;
  change_sign: string;
  change_pct: string;
  volume: string;
  open: string;
  high: string;
  low: string;
  w52_high: string;
  w52_low: string;
  per: string;
  pbr: string;
  eps: string;
  market_cap: string;
  _raw: Record<string, string>;
}

interface FlucRow {
  stck_shrn_iscd: string;
  hts_kor_isnm: string;
  stck_prpr: string;
  prdy_ctrt: string;
  acml_vol: string;
}

interface FlucResponse {
  rows: FlucRow[];
  count: number;
}

async function loadQuote(symbol: string): Promise<QuoteData | null> {
  try {
    return await fetchEnvelope<QuoteData>(`/api/v1/execute/quote/${symbol}`, {
      revalidate: 30,
    });
  } catch {
    return null;
  }
}

async function loadFluc(): Promise<FlucResponse | null> {
  try {
    return await fetchEnvelope<FlucResponse>(
      "/api/v1/execute/fluctuation?top_n=20&rank_sort=0",
      { revalidate: 60 },
    );
  } catch {
    return null;
  }
}

const FMT_INT = (v: string | null | undefined) => {
  if (!v) return "—";
  const n = Number(v);
  return isFinite(n) ? n.toLocaleString() : v;
};
const FMT_PCT = (v: string | null | undefined) =>
  v == null ? "—" : `${Number(v).toFixed(2)}%`;

export default async function Page() {
  const [q, fluc] = await Promise.all([loadQuote("005930"), loadFluc()]);

  const cells = q
    ? [
        { label: "005930 삼성전자", value: FMT_INT(q.price), delta: FMT_PCT(q.change_pct), tone: Number(q.change) >= 0 ? "pos" as const : "neg" as const },
        { label: "시가", value: FMT_INT(q.open) },
        { label: "고가", value: FMT_INT(q.high), tone: "pos" as const },
        { label: "저가", value: FMT_INT(q.low), tone: "neg" as const },
        { label: "52W High", value: FMT_INT(q.w52_high) },
        { label: "PER", value: q.per ?? "—", delta: `PBR ${q.pbr ?? "—"}` },
      ]
    : [];

  return (
    <DensePage tab="Execute" current="국내주식" title="국내주식" meta="KIS OPEN API · KOSPI/KOSDAQ · live">
      {q ? (
        <SummaryCards cells={cells} />
      ) : (
        <EmptyState title="KIS 연결 실패" note="005930 현재가 조회 실패 — Execute/health 에서 OAuth 상태를 확인하세요." />
      )}

      <div className="panel" style={{ marginTop: 12 }}>
        <div className="panel-header">
          <h2>등락률 상위 Top 20</h2>
          <span className="muted">FHPST01700000 · KRX · 실데이터</span>
        </div>
        <div className="panel-body p0">
          {!fluc || fluc.rows.length === 0 ? (
            <EmptyState title="랭킹 데이터 없음" note="KIS fluctuation 응답이 비어있습니다." />
          ) : (
            <table className="mini">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Ticker</th>
                  <th>Name</th>
                  <th style={{ textAlign: "right" }}>Price</th>
                  <th style={{ textAlign: "right" }}>Chg%</th>
                  <th style={{ textAlign: "right" }}>Vol</th>
                </tr>
              </thead>
              <tbody>
                {fluc.rows.slice(0, 20).map((r, i) => (
                  <tr key={`${r.stck_shrn_iscd}-${i}`}>
                    <td>{i + 1}</td>
                    <td>{r.stck_shrn_iscd}</td>
                    <td>{r.hts_kor_isnm}</td>
                    <td style={{ textAlign: "right" }}>{FMT_INT(r.stck_prpr)}</td>
                    <td style={{ textAlign: "right", color: Number(r.prdy_ctrt) >= 0 ? "var(--pos, #3b8f57)" : "var(--neg, #b8434b)" }}>
                      {FMT_PCT(r.prdy_ctrt)}
                    </td>
                    <td style={{ textAlign: "right" }}>{FMT_INT(r.acml_vol)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </DensePage>
  );
}
