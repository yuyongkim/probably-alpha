// StatusCards — platform health at a glance.
import type { AdminStatus } from "@/types/admin";

interface Props {
  status: AdminStatus;
}

function mb(bytes: number | null | undefined): string {
  if (!bytes) return "—";
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function gb(bytes: number | null | undefined): string {
  if (!bytes) return "—";
  if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(2)} GB`;
  return `${(bytes / 1e6).toFixed(1)} MB`;
}

export function StatusCards({ status }: Props) {
  // Backend currently returns the identity + secrets envelope without the
  // heavier DB introspection payload. Stay defensive so the page renders
  // even when ``db`` is absent (partial deploy, pre-migration, etc.).
  const db = status.db ?? ({} as AdminStatus["db"]);
  const rag = db?.rag;
  const rows = db?.rows ?? ({} as Record<string, number>);
  const cards: Array<[string, string, string?]> = [
    ["Owner", status.owner_id],
    ["Shared Env", status.shared_env_loaded ? "loaded" : "missing"],
    ["DB size", gb(db?.db_size_bytes)],
    ["OHLCV rows", (rows.ohlcv ?? 0).toLocaleString()],
    ["OHLCV symbols", (rows.ohlcv_symbols ?? 0).toLocaleString()],
    ["Universe", (rows.universe ?? 0).toLocaleString()],
    ["Financials PIT", (rows.financials_pit ?? 0).toLocaleString()],
    ["Observations", (rows.observations ?? 0).toLocaleString()],
    ["Filings", (rows.filings ?? 0).toLocaleString()],
    ["RAG chunks", rag?.chunks?.toLocaleString() ?? "—"],
    ["RAG docs", `${rag?.files_indexed ?? "?"}/${rag?.files_total ?? "?"}`],
    ["RAG size", mb(rag?.bytes)],
  ];
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
      {cards.map(([k, v]) => (
        <div
          key={k}
          className="rounded-md border px-3 py-2"
          style={{ background: "var(--surface)", borderColor: "var(--border)" }}
        >
          <div className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
            {k}
          </div>
          <div className="display text-base mono">{v}</div>
        </div>
      ))}
    </div>
  );
}
