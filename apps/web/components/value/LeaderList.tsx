// Reusable leaderboard for MoS / Deep Value / EV-EBITDA / ROIC / FCF Yield.
// Extra column is configurable per page.

import { DenseTable, type DenseColumn } from "@/components/shared/DenseTable";
import type { LeaderRow } from "@/types/value";

const num = (v: unknown, digits = 2) => {
  if (typeof v !== "number") return "–";
  return v.toLocaleString(undefined, { maximumFractionDigits: digits });
};

export interface LeaderListProps {
  rows: LeaderRow[];
  title: string;
  subtitle?: string;
  metricKey: string;
  metricHeader: string;
  metricFormat?: (v: unknown) => string;
  metricDigits?: number;
}

export function LeaderList({
  rows,
  title,
  subtitle,
  metricKey,
  metricHeader,
  metricFormat,
  metricDigits = 2,
}: LeaderListProps) {
  const cols: DenseColumn<LeaderRow>[] = [
    { key: "symbol", header: "Sym" },
    { key: "name", header: "Name" },
    { key: "sector", header: "Sector" },
    { key: "close", header: "Close", align: "right", format: (v) => num(v, 0) },
    {
      key: metricKey as keyof LeaderRow & string,
      header: metricHeader,
      align: "right",
      format: metricFormat ? ((v) => metricFormat(v)) : ((v) => num(v, metricDigits)),
    },
  ];
  return (
    <section>
      <header className="mb-3">
        <h2 className="display text-2xl">{title}</h2>
        {subtitle && <p className="text-sm text-[color:var(--fg-muted)]">{subtitle}</p>}
      </header>
      <DenseTable
        columns={cols}
        rows={rows}
        rowKey={(r) => r.symbol}
        emptyLabel="데이터 없음"
      />
    </section>
  );
}
