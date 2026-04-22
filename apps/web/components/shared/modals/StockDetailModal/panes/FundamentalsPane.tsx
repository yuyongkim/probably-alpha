// FundamentalsPane — 8Q trailing earnings table (mock).
"use client";

interface Props {
  symbol: string;
}

interface Q {
  quarter: string;
  rev: string;     // 매출
  op: string;      // 영업이익
  np: string;      // 당기순이익
  eps: string;     // EPS
  yoy: number;     // EPS YoY %
}

const SAMPLE: Q[] = [
  { quarter: "25Q2E", rev: "4.18조", op: "8,420억", np: "6,140억", eps: "1,842", yoy: 38 },
  { quarter: "25Q1",  rev: "3.92조", op: "7,610억", np: "5,580억", eps: "1,674", yoy: 32 },
  { quarter: "24Q4",  rev: "3.74조", op: "6,940억", np: "5,120억", eps: "1,534", yoy: 28 },
  { quarter: "24Q3",  rev: "3.52조", op: "6,210억", np: "4,540억", eps: "1,362", yoy: 22 },
  { quarter: "24Q2",  rev: "3.28조", op: "5,480억", np: "3,980억", eps: "1,194", yoy: 18 },
  { quarter: "24Q1",  rev: "3.04조", op: "4,820억", np: "3,510억", eps: "1,052", yoy: 12 },
  { quarter: "23Q4",  rev: "2.84조", op: "4,210억", np: "3,080억", eps: "924", yoy: 4 },
  { quarter: "23Q3",  rev: "2.72조", op: "3,940억", np: "2,850억", eps: "854", yoy: -2 },
];

export function FundamentalsPane({ symbol }: Props) {
  return (
    <div>
      <div className="text-[11px] text-[color:var(--fg-muted)] mb-2">
        Trailing 8Q · KRW · mock (DART/연결 재무, pending adapter wiring · {symbol})
      </div>
      <table className="w-full text-[11.5px] border-collapse">
        <thead>
          <tr className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
            <th className="py-1.5 px-2 text-left font-medium">Q</th>
            <th className="py-1.5 px-2 text-right font-medium">매출</th>
            <th className="py-1.5 px-2 text-right font-medium">영업이익</th>
            <th className="py-1.5 px-2 text-right font-medium">당기순이익</th>
            <th className="py-1.5 px-2 text-right font-medium">EPS</th>
            <th className="py-1.5 px-2 text-right font-medium">YoY</th>
          </tr>
        </thead>
        <tbody>
          {SAMPLE.map((q) => (
            <tr key={q.quarter} style={{ borderTop: "1px solid var(--border-soft)" }}>
              <td className="py-1.5 px-2 mono">{q.quarter}</td>
              <td className="py-1.5 px-2 mono text-right">{q.rev}</td>
              <td className="py-1.5 px-2 mono text-right">{q.op}</td>
              <td className="py-1.5 px-2 mono text-right">{q.np}</td>
              <td className="py-1.5 px-2 mono text-right font-medium">{q.eps}</td>
              <td
                className="py-1.5 px-2 mono text-right"
                style={{ color: q.yoy >= 0 ? "var(--pos)" : "var(--neg)" }}
              >
                {q.yoy >= 0 ? `+${q.yoy}%` : `${q.yoy}%`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
