"use client";

interface Props {
  asOf?: string;
}

export function HeroHeader({ asOf }: Props) {
  const today = new Date();
  const todayStr = today.toISOString().slice(0, 10);
  const asOfDate = asOf ? new Date(asOf) : null;
  const ageDays = asOfDate
    ? Math.floor((today.getTime() - asOfDate.getTime()) / 86400000)
    : null;
  const isStale = ageDays !== null && ageDays > 2;

  return (
    <>
      <div className="flex items-baseline justify-between flex-wrap gap-2 mb-4">
        <h1 className="display text-4xl">probably-alpha</h1>
        <div className="flex items-baseline gap-3">
          <span className="mono text-[11px] text-[color:var(--fg-muted)]">
            {todayStr} · {today.toLocaleDateString("ko-KR", { weekday: "long" })}
          </span>
          {asOf && (
            <span
              className="mono text-[10px] px-1.5 py-[1px] rounded border"
              style={{
                borderColor: isStale ? "var(--neg)" : "var(--border)",
                color: isStale ? "var(--neg)" : "var(--fg-muted)",
                background: "var(--bg)",
              }}
              title={`data as-of ${asOf}, today is ${todayStr}`}
            >
              데이터 as-of {asOf}
              {isStale ? ` (${ageDays}d stale)` : ""}
            </span>
          )}
        </div>
      </div>
      <p className="text-[color:var(--fg-muted)] mb-6 text-[13px] leading-relaxed max-w-3xl">
        한국 주식 시장용 6-탭 통합 리서치 플랫폼. Chartist로 주도주/섹터를 스캔하고,
        Quant/Value로 팩터·재무를 분석하며, Execute로 KIS를 통해 주문·관찰한다.
        Research 탭의 AI 어시스턴트는 도서 41K · 한은 367K · 증권사 104K 청크의
        3-layer RAG 위에서 Haiku 4.5가 답한다.
      </p>
    </>
  );
}
