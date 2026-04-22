import {
  Breadcrumb,
  PageHeader,
  SummaryRow,
  Panel,
  Stub,
} from "@/components/chartist/common/MockupPrimitives";
import { KIWOOM_CONDITIONS } from "@/lib/chartist/mockData";

export function KiwoomCondView() {
  const totalPass = KIWOOM_CONDITIONS.reduce((s, c) => s + c.pass, 0);
  return (
    <div>
      <Breadcrumb trail={["Chartist", "키움 조건식"]} />
      <PageHeader
        title="키움 조건식 7종"
        meta="MA 골든크로스 · 거래량 급증 · RSI · 볼린저 · MACD · ..."
      />
      <SummaryRow
        cells={[
          { label: "조건식 수", value: "7", delta: "활성" },
          {
            label: "총 Pass",
            value: totalPass.toString(),
            delta: "합산",
            tone: "pos",
          },
          { label: "최대 Pass", value: "48", delta: "거래량 급증 2배+", tone: "pos" },
          { label: "교집합 (4+)", value: "18", delta: "매매 신호", tone: "pos" },
          { label: "30D 정확도", value: "62.4%", delta: "8 / 13", tone: "pos" },
          { label: "소스", value: "QuantPlatform", delta: "이식 예정" },
        ]}
      />

      <Panel
        title="조건식 현황"
        subtitle="7 / 각 조건식 통과 종목 수"
        bodyPad={false}
      >
        <table className="mini w-full text-[11px] border-collapse">
          <thead>
            <tr>
              <th className="py-1.5 px-2 text-[9.5px] uppercase tracking-widest font-medium text-[color:var(--muted)] border-b text-left">
                #
              </th>
              <th className="py-1.5 px-2 text-[9.5px] uppercase tracking-widest font-medium text-[color:var(--muted)] border-b text-left">
                조건식
              </th>
              <th className="py-1.5 px-2 text-[9.5px] uppercase tracking-widest font-medium text-[color:var(--muted)] border-b text-left">
                설명
              </th>
              <th className="py-1.5 px-2 text-[9.5px] uppercase tracking-widest font-medium text-[color:var(--muted)] border-b text-right">
                Pass
              </th>
            </tr>
          </thead>
          <tbody>
            {KIWOOM_CONDITIONS.map((c) => (
              <tr
                key={c.id}
                style={{ borderBottom: "1px solid var(--border-soft)" }}
              >
                <td className="py-1 px-2 mono text-[10.5px] text-[color:var(--fg-muted)]">
                  {c.id}
                </td>
                <td className="py-1 px-2 text-[12px]">{c.name}</td>
                <td className="py-1 px-2 text-[11px] text-[color:var(--fg-muted)]">
                  {c.desc}
                </td>
                <td className="py-1 px-2 mono text-[11.5px] text-right tabular-nums">
                  {c.pass}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>

      <div className="mt-3">
        <Stub
          icon="Ω"
          title="7개 중 4개 이상 충족 → 매매 신호"
          desc="QuantPlatform의 kiwoom_condition_analyzer 이식. MA 골든크로스, 거래량 급증 등 조합으로 매수 신호 생성. SEPA와 교차 검증."
          chips={["QuantPlatform 흡수"]}
        />
      </div>
    </div>
  );
}
