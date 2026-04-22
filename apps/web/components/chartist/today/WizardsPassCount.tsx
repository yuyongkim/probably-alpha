// WizardsPassCount — 7 rows: 6 trader presets + intersection.
// Counts 오늘 통과 수 · % of universe · delta vs 어제.
import type { WizardCount } from "@/types/chartist";

interface Props {
  items: WizardCount[];
}

const TH =
  "py-1.5 px-2 text-[9.5px] uppercase tracking-widest font-medium text-[color:var(--muted)] border-b";
const TD_NUM = "py-1 px-2 mono text-[11px] text-right tabular-nums";

function pct(pass: number, total: number): string {
  if (!total) return "—";
  return `${((pass / total) * 100).toFixed(2)}%`;
}

function deltaStyle(v: number): string {
  if (v > 0) return "var(--pos)";
  if (v < 0) return "var(--neg)";
  return "var(--neutral)";
}

function deltaText(v: number): string {
  if (v > 0) return `+${v}`;
  return v.toString();
}

export function WizardsPassCount({ items }: Props) {
  return (
    <div
      className="rounded-md border overflow-hidden"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div
        className="flex items-baseline justify-between px-3 py-2 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <h2 className="display text-base">Market Wizards Pass Count</h2>
        <span className="text-[10px] text-[color:var(--fg-muted)]">
          오늘 각 프리셋 통과 종목 수
        </span>
      </div>
      <table className="w-full text-[11.5px] border-collapse">
        <thead>
          <tr>
            <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>
              Preset
            </th>
            <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>
              조건
            </th>
            <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>
              Pass
            </th>
            <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>
              %
            </th>
            <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>
              Δ vs 어제
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((w) => (
            <tr
              key={w.name}
              style={{ borderBottom: "1px solid var(--border-soft)" }}
              className="hover:bg-[color:var(--surface-2)]"
            >
              <td className="py-1 px-2 font-medium">{w.name}</td>
              <td className="py-1 px-2 text-[color:var(--fg-muted)]">{w.condition}</td>
              <td className={TD_NUM}>{w.pass_count}</td>
              <td className={TD_NUM}>{pct(w.pass_count, w.total)}</td>
              <td className={TD_NUM} style={{ color: deltaStyle(w.delta_vs_yesterday) }}>
                {deltaText(w.delta_vs_yesterday)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
