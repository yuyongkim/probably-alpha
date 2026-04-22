// WizardPage — reusable page template for /chartist/wizards/[name].
// Hydrates the live API's pass list but falls back to the mockup mock
// for summary / conditions / playbook so each Wizard page hits the
// mockup's density even when only counts exist in the API yet.
import type { WizardDetail } from "@/types/chartist";
import type { WizardConfig } from "@/lib/wizards";
import { WIZARD_MOCKS } from "@/lib/chartist/mockData";
import {
  Breadcrumb,
  PageHeader,
  QuoteStrip,
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
  toneColorNumber,
  signed,
} from "@/components/chartist/common/MockupPrimitives";
import { TickerName } from "@/components/shared/TickerName";

interface Props {
  detail: WizardDetail;
  config: WizardConfig;
}

export function WizardPage({ detail, config }: Props) {
  const mock = WIZARD_MOCKS[config.key];
  const hasLiveRows = detail.rows && detail.rows.length > 0;

  return (
    <div>
      <Breadcrumb
        trail={["Chartist", "Market Wizards", config.name]}
      />
      <PageHeader
        title={config.name}
        meta={
          mock?.pageMeta ??
          `${detail.as_of} CLOSE · ${detail.count}개 통과 · ${detail.condition}`
        }
      />
      <QuoteStrip
        quote={mock?.quote ?? config.quote}
        attr={mock?.quoteAttr}
      />

      {mock && <SummaryRow cells={mock.summary} />}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* Left: live API rows (preferred) or mock rows */}
        <Panel
          title={`${config.name.split(" ·")[0]} 통과 종목`}
          subtitle={hasLiveRows ? `${detail.rows.length}개 · 실시간` : "mock preview"}
          bodyPad={false}
        >
          {hasLiveRows ? (
            <LiveTable detail={detail} />
          ) : mock ? (
            <MockTable mock={mock} />
          ) : (
            <div className="p-4 text-[11px] text-[color:var(--fg-muted)]">
              No data
            </div>
          )}
        </Panel>

        {/* Right: conditions + playbook */}
        <Panel
          title={mock?.sideTitle ?? "조건 통과율"}
          subtitle={mock?.sideSubtitle ?? "Rules"}
        >
          {mock && mock.conditions.length > 0 ? (
            <CondList rows={mock.conditions} />
          ) : (
            <ol className="list-decimal pl-5 flex flex-col gap-1 text-[12px] text-[color:var(--fg)]">
              {config.rules.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ol>
          )}
          {mock && (
            <div
              className="mt-3 p-3 rounded-md text-[11.5px] leading-relaxed"
              style={{ background: "var(--bg)", color: "var(--fg-muted)" }}
            >
              <strong style={{ color: "var(--fg)" }}>Playbook:</strong>{" "}
              {mock.playbook}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}

function LiveTable({ detail }: { detail: WizardDetail }) {
  return (
    <table className={MINI_TABLE_CLS}>
      <thead>
        <tr>
          <th className={MINI_TH}>#</th>
          <th className={MINI_TH}>Ticker</th>
          <th className={MINI_TH}>Market</th>
          <th className={MINI_TH}>Sector</th>
          <th className={MINI_TH_NUM}>Close</th>
          <th className={MINI_TH_NUM}>1D</th>
          <th className={MINI_TH_NUM}>Vol×</th>
          <th className={MINI_TH}>왜 통과?</th>
        </tr>
      </thead>
      <tbody>
        {detail.rows.map((h, i) => (
          <tr
            key={h.symbol}
            style={MINI_ROW_BORDER}
            className="hover:bg-[color:var(--surface-2)]"
          >
            <td className={`${MINI_TD} mono text-[10px] text-[color:var(--fg-muted)]`}>
              {i + 1}
            </td>
            <td className={MINI_TD}>
              <TickerName symbol={h.symbol} name={h.name} sector={h.sector} />
              <span className="mono ml-2 text-[10px] text-[color:var(--fg-muted)]">
                {h.symbol}
              </span>
            </td>
            <td className={`${MINI_TD} text-[10.5px] text-[color:var(--fg-muted)]`}>
              {h.market}
            </td>
            <td className={`${MINI_TD} text-[10.5px]`}>{h.sector}</td>
            <td className={MINI_TD_NUM}>{h.close.toLocaleString()}</td>
            <td
              className={MINI_TD_NUM}
              style={{ color: toneColorNumber(h.pct_1d) }}
            >
              {signed(h.pct_1d)}
            </td>
            <td className={MINI_TD_NUM}>{h.vol_x.toFixed(1)}×</td>
            <td className={`${MINI_TD} text-[10.5px] text-[color:var(--fg-muted)]`}>
              {h.reason}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function MockTable({ mock }: { mock: typeof WIZARD_MOCKS[string] }) {
  return (
    <table className={MINI_TABLE_CLS}>
      <thead>
        <tr>
          {mock.passHeaders.map((h) => (
            <th
              key={h.key}
              className={h.align === "right" ? MINI_TH_NUM : MINI_TH}
            >
              {h.label}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {mock.passRows.map((row, i) => (
          <tr key={i} style={MINI_ROW_BORDER}>
            {mock.passHeaders.map((h) => {
              const v = row[h.key];
              if (h.key === "name") {
                return (
                  <td key={h.key} className={MINI_TD}>
                    <TickerName symbol="" name={String(v)} />
                    {row.code && (
                      <span className="mono ml-1.5 text-[10px] text-[color:var(--fg-muted)]">
                        {String(row.code)}
                      </span>
                    )}
                  </td>
                );
              }
              if (h.key === "sector") {
                return (
                  <td key={h.key} className={MINI_TD}>
                    <Chip tone="accent">{String(v)}</Chip>
                  </td>
                );
              }
              if (h.key === "status" || h.key === "stage" || h.key === "line" || h.key === "pyramid" || h.key === "pattern" || h.key === "sub" || h.key === "angle") {
                let t: "pos" | "amber" | "neg" | "neutral" = "neutral";
                const sv = String(v);
                if (sv.includes("BROKE") || sv.includes("Confirmed") || sv.includes("Stage 2") || sv.includes("상승") || sv.includes("급상승")) t = "pos";
                else if (sv.includes("READY") || sv.includes("Testing") || sv.includes("VCP") || sv.includes("Lv 2") || sv.includes("Lv 3") || sv.includes("완만") || sv.includes("초기") || sv.includes("중기") || sv.includes("성숙") || sv.includes("Late")) t = "amber";
                else if (sv.includes("STOP") || sv.includes("WAIT")) t = sv.includes("STOP") ? "neg" : "neutral";
                return (
                  <td key={h.key} className={MINI_TD}>
                    <Chip tone={t}>{sv}</Chip>
                  </td>
                );
              }
              return (
                <td
                  key={h.key}
                  className={h.align === "right" ? MINI_TD_NUM : MINI_TD}
                >
                  {String(v ?? "")}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
