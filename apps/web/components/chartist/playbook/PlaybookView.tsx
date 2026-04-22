import {
  Breadcrumb,
  PageHeader,
  SummaryRow,
  Panel,
  QuoteStrip,
  CondList,
} from "@/components/chartist/common/MockupPrimitives";
import {
  PLAYBOOK_SUMMARY,
  PLAYBOOK_CHECKS,
  PLAYBOOK_STATS,
} from "@/lib/chartist/mockData";

export function PlaybookView() {
  return (
    <div>
      <Breadcrumb trail={["Chartist", "Playbook"]} />
      <PageHeader title="Pre-trade Playbook" meta="개인 체크리스트 · 충동매매 방지" />
      <QuoteStrip
        quote="The goal of a successful trader is to make the best trades. Money is secondary."
        attr="— Alexander Elder · Trading for a Living"
      />
      <SummaryRow cells={PLAYBOOK_SUMMARY} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Panel title="Pre-trade 체크리스트" subtitle="진입 전 반드시 확인">
          <div className="flex flex-col gap-1.5">
            {PLAYBOOK_CHECKS.map((c) => (
              <div
                key={c.n}
                className="check-row flex items-center gap-2.5 text-[11.5px]"
              >
                <span
                  className={`check-box inline-block w-4 h-4 rounded border ${c.done ? "on" : ""}`}
                  style={{
                    background: c.done ? "var(--pos)" : "transparent",
                    borderColor: c.done ? "var(--pos)" : "var(--border)",
                  }}
                />
                <span
                  className="cond-label flex-1"
                  style={{
                    color: c.done ? "var(--fg)" : "var(--fg-muted)",
                  }}
                >
                  {c.label}
                </span>
                <span
                  className="check-time mono text-[10px] text-[color:var(--fg-muted)]"
                  style={{ minWidth: 40, textAlign: "right" }}
                >
                  {c.time}
                </span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="항목별 준수율 (30일)" subtitle="통계">
          <CondList
            rows={PLAYBOOK_STATS.map((s) => ({
              icon: s.n,
              label: s.label,
              pct: s.pct,
              amber: s.amber,
              labelRight: `${s.pct}%`,
              iconTone: s.amber ? "amber" : undefined,
            }))}
          />
        </Panel>
      </div>
    </div>
  );
}
