import {
  Breadcrumb,
  PageHeader,
  SummaryRow,
  Panel,
  Chip,
  CondList,
  MINI_TABLE_CLS,
  MINI_TH,
  MINI_TH_NUM,
  MINI_TD,
  MINI_TD_NUM,
  MINI_ROW_BORDER,
} from "@/components/chartist/common/MockupPrimitives";
import { TickerName } from "@/components/shared/TickerName";
import {
  JOURNAL_SUMMARY,
  JOURNAL_ROWS,
  JOURNAL_MISTAKES,
} from "@/lib/chartist/mockData";

export function JournalView() {
  return (
    <div>
      <Breadcrumb trail={["Chartist", "매매일지"]} />
      <PageHeader
        title="매매일지"
        meta="TRADE JOURNAL · 30 DAYS · 17 TRADES · WIN RATE 64.7%"
      />
      <SummaryRow cells={JOURNAL_SUMMARY} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Panel title="최근 매매 기록" subtitle="진입 사유 + 결과 + 교훈" bodyPad={false}>
          <table className={MINI_TABLE_CLS}>
            <thead>
              <tr>
                <th className={MINI_TH}>Date</th>
                <th className={MINI_TH}>Ticker</th>
                <th className={MINI_TH}>Type</th>
                <th className={MINI_TH_NUM}>손익%</th>
                <th className={MINI_TH_NUM}>보유일</th>
                <th className={MINI_TH}>Wizard</th>
                <th className={MINI_TH}>교훈</th>
              </tr>
            </thead>
            <tbody>
              {JOURNAL_ROWS.map((r) => (
                <tr key={r.date + r.name} style={MINI_ROW_BORDER}>
                  <td className={`${MINI_TD} mono text-[10.5px]`}>{r.date}</td>
                  <td className={MINI_TD}>
                    <TickerName symbol="" name={r.name} />
                  </td>
                  <td className={MINI_TD}>
                    <Chip tone={r.tone === "pos" ? "pos" : "neg"}>{r.type}</Chip>
                  </td>
                  <td
                    className={MINI_TD_NUM}
                    style={{ color: r.pl > 0 ? "var(--pos)" : "var(--neg)" }}
                  >
                    {r.pl > 0 ? "+" : ""}
                    {r.pl.toFixed(1)}
                  </td>
                  <td className={MINI_TD_NUM}>{r.days}</td>
                  <td className={`${MINI_TD} text-[11px]`}>{r.wiz}</td>
                  <td
                    className={`${MINI_TD} text-[10.5px] text-[color:var(--fg-muted)]`}
                  >
                    {r.note}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel title="실수 카테고리" subtitle="30일 6건 손실 분석">
          <CondList
            rows={JOURNAL_MISTAKES.map((m) => ({
              icon: m.icon,
              iconTone:
                m.tone === "neg" ? "neg" : m.tone === "amber" ? "amber" : "pos",
              label: m.label,
              pct: m.pct,
              amber: m.tone !== "pos",
              labelRight: m.txt,
            }))}
          />
          <div
            className="mt-3 p-2.5 rounded-md text-[11px] leading-relaxed"
            style={{ background: "var(--accent-soft)", color: "var(--fg)" }}
          >
            <strong>패턴:</strong> 거래량 확증 부족이 반복 실수 1위. Playbook
            체크리스트 강화 필요.
          </div>
        </Panel>
      </div>
    </div>
  );
}
