// Execute · Positions — live wiring to /api/v1/execute/overview.
// Overview endpoint currently returns positions=[] until KIS inquire-balance
// TR lands. We surface the backbone status + empty state so the page is no
// longer a pure placeholder.
// ROADMAP: full balance/positions require KIS inquire-balance TR. See
//          apps/api/routers/execute/__init__.py (execute_overview).
import { DensePage } from "@/components/shared/DensePage";
import { EmptyState } from "@/components/shared/EmptyState";
import { fetchEnvelope } from "@/lib/api";

export const revalidate = 60;

interface OverviewLive {
  account_no: string | null;
  product_code: string;
  env: string;
  health: { ok: boolean; latency_ms: number | null; last_error: string | null };
  positions: Array<Record<string, unknown>>;
  note: string;
}

async function load(): Promise<OverviewLive | null> {
  try {
    return await fetchEnvelope<OverviewLive>("/api/v1/execute/overview", {
      revalidate: 60,
    });
  } catch {
    return null;
  }
}

export default async function Page() {
  const live = await load();
  const healthOk = live?.health?.ok === true;
  const acct = live?.account_no
    ? `${live.account_no}-${live.product_code ?? "01"}`
    : "계좌 미설정";
  const meta = live
    ? `KIS ${live.env} · ${acct} · ${healthOk ? "OAuth OK" : "OAuth FAIL"}`
    : "KIS Overview 응답 없음";

  return (
    <DensePage
      tab="Execute"
      current="보유 포지션"
      title="보유 포지션 전체"
      meta={meta}
    >
      {!live ? (
        <EmptyState
          variant="warn"
          title="Execute 백본 연결 실패"
          note="/api/v1/execute/overview 응답을 받지 못했습니다. API 서버와 KIS OAuth 상태를 확인하세요."
          hint="GET /api/v1/execute/overview"
        />
      ) : live.positions.length === 0 ? (
        <EmptyState
          title="보유 포지션 없음 (또는 아직 조회 불가)"
          note={live.note}
          hint="ROADMAP: KIS inquire-balance TR 연결 후 실제 포지션 노출"
        />
      ) : (
        <div className="panel">
          <div className="panel-header">
            <h2>보유 포지션 {live.positions.length}건</h2>
            <span className="muted">KIS inquire-balance</span>
          </div>
          <div className="panel-body p0">
            <table className="mini">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th style={{ textAlign: "right" }}>수량</th>
                  <th style={{ textAlign: "right" }}>평단</th>
                  <th style={{ textAlign: "right" }}>현재가</th>
                  <th style={{ textAlign: "right" }}>평가손익</th>
                </tr>
              </thead>
              <tbody>
                {live.positions.map((p, i) => (
                  <tr key={i}>
                    <td className="mono">{String(p.symbol ?? "—")}</td>
                    <td style={{ textAlign: "right" }}>{String(p.qty ?? "—")}</td>
                    <td style={{ textAlign: "right" }}>{String(p.avg ?? "—")}</td>
                    <td style={{ textAlign: "right" }}>{String(p.last ?? "—")}</td>
                    <td style={{ textAlign: "right" }}>{String(p.pnl ?? "—")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </DensePage>
  );
}
