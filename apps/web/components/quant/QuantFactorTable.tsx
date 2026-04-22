// Factor-screener table. All numeric columns right-aligned; percentile
// ranks rendered 0–100. Uses the shared DenseTable primitive.

import { DenseTable, type DenseColumn } from "@/components/shared/DenseTable";
import type { FactorRow } from "@/types/quant";

const pct = (v: number | null | undefined) =>
  v == null ? "–" : `${(v * 100).toFixed(0)}`;

const num = (v: number | null | undefined) =>
  v == null ? "–" : v.toLocaleString();

const COLUMNS: DenseColumn<FactorRow>[] = [
  { key: "symbol", header: "Symbol" },
  { key: "name", header: "Name" },
  { key: "sector", header: "Sector" },
  { key: "market", header: "Mkt", width: "60px" },
  { key: "close", header: "Close", align: "right", format: (v) => num(v as number | null) },
  {
    key: "momentum",
    header: "MOM",
    align: "right",
    format: (v) => pct(v as number | null),
  },
  { key: "value", header: "VAL", align: "right", format: (v) => pct(v as number | null) },
  {
    key: "quality",
    header: "QUAL",
    align: "right",
    format: (v) => pct(v as number | null),
  },
  {
    key: "low_vol",
    header: "LVOL",
    align: "right",
    format: (v) => pct(v as number | null),
  },
  {
    key: "growth",
    header: "GROW",
    align: "right",
    format: (v) => pct(v as number | null),
  },
  {
    key: "composite",
    header: "COMP",
    align: "right",
    format: (v) => pct(v as number | null),
    tone: (r) =>
      r.composite == null
        ? undefined
        : r.composite > 0.7
        ? "pos"
        : r.composite < 0.3
        ? "neg"
        : "neutral",
  },
];

export function QuantFactorTable({ rows }: { rows: FactorRow[] }) {
  return (
    <DenseTable
      columns={COLUMNS}
      rows={rows}
      rowKey={(r) => r.symbol}
      emptyLabel="팩터 데이터 없음"
    />
  );
}
