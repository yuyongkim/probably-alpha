// Value · Disclosures — DART 자동 분석 요약 (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { Panel } from "@/components/shared/Panel";
import { DISCLOSURE_ROWS } from "@/lib/value/mockData";

const chipClass = (s: string) =>
  s === "Positive" ? "chip pos" : s === "Risk" || s === "Negative" ? "chip neg" : "chip";

export default function ValueDisclosuresPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "DART 공시", current: true }]}
        title="DART 자동 분석"
        meta="PDF → STRUCTURED · 최근 24h"
      />
      <Panel>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {DISCLOSURE_ROWS.map((r, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                gap: 10,
                padding: 12,
                background: "var(--bg)",
                borderRadius: 8,
                alignItems: "flex-start",
              }}
            >
              <span className="chip accent">{r.type}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 500, fontSize: 13 }}>{r.title}</div>
                <div className="reason-text">{r.detail}</div>
              </div>
              <span className={chipClass(r.sentiment)}>{r.sentiment}</span>
            </div>
          ))}
        </div>
      </Panel>
    </>
  );
}
