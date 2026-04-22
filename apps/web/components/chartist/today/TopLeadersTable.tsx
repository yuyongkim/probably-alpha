// TopLeadersTable — 10 leader stocks, dense Bloomberg-style row.
// Modeled on mockup `table.mini`. Kept self-contained for the slice;
// promote to shared/DenseTable once a second consumer needs the same
// cell renderers (ticker pair, pattern chip, tone-colored mono cells).
import type { Leader } from "@/types/chartist";

interface Props {
  leaders: Leader[];
}

function signed(v: number): string {
  return v > 0 ? `+${v.toFixed(2)}` : v.toFixed(2);
}

function toneStyle(v: number): string {
  if (v > 0) return "var(--pos)";
  if (v < 0) return "var(--neg)";
  return "var(--neutral)";
}

function patternChipClass(p: string): string {
  if (p === "VCP") {
    return "border border-[color:var(--accent)] text-[color:var(--accent)] bg-[color:var(--accent-soft)]";
  }
  return "border border-[color:var(--border-soft)] text-[color:var(--fg-muted)]";
}

const TH =
  "py-1.5 px-2 text-[9.5px] uppercase tracking-widest font-medium text-[color:var(--muted)] border-b";
const TD_NUM = "py-1 px-2 mono text-[11px] text-right tabular-nums";

export function TopLeadersTable({ leaders }: Props) {
  return (
    <div
      className="rounded-md border overflow-hidden"
      style={{
        background: "var(--surface)",
        borderColor: "var(--border)",
      }}
    >
      <div
        className="flex items-baseline justify-between px-3 py-2 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <h2 className="display text-base">Top Leaders</h2>
        <span className="text-[10px] text-[color:var(--fg-muted)]">
          LS · TT · RS · 1D · 5D · 1M · Pat.
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[11.5px] border-collapse">
          <thead>
            <tr>
              <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>Ticker</th>
              <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>Sector</th>
              <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>LS</th>
              <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>TT</th>
              <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>1D</th>
              <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>5D</th>
              <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>Vol×</th>
              <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>Pat.</th>
            </tr>
          </thead>
          <tbody>
            {leaders.map((l) => (
              <tr
                key={l.symbol}
                className="hover:bg-[color:var(--surface-2)]"
                style={{ borderBottom: "1px solid var(--border-soft)" }}
              >
                <td className="py-1 px-2">
                  <span className="font-medium">{l.name}</span>
                  <span className="mono ml-2 text-[10.5px] text-[color:var(--fg-muted)]">
                    {l.symbol}
                  </span>
                </td>
                <td className="py-1 px-2">
                  <span className="inline-block px-1.5 py-[1px] text-[10px] rounded border border-[color:var(--accent)] text-[color:var(--accent)] bg-[color:var(--accent-soft)]">
                    {l.sector}
                  </span>
                </td>
                <td className={TD_NUM}>{l.leader_score.toFixed(2)}</td>
                <td className={TD_NUM}>{l.trend_template}</td>
                <td className={TD_NUM} style={{ color: toneStyle(l.d1) }}>{signed(l.d1)}</td>
                <td className={TD_NUM} style={{ color: toneStyle(l.d5) }}>{signed(l.d5)}</td>
                <td className={TD_NUM}>{l.vol_x.toFixed(1)}×</td>
                <td className="py-1 px-2">
                  <span className={`inline-block px-1.5 py-[1px] text-[10px] rounded ${patternChipClass(l.pattern)}`}>
                    {l.pattern}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
