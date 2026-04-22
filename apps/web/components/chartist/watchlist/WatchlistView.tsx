import {
  Breadcrumb,
  PageHeader,
  SummaryRow,
  Panel,
  Chip,
  ActivityLog,
  MINI_TABLE_CLS,
  MINI_TH,
  MINI_TH_NUM,
  MINI_TD,
  MINI_TD_NUM,
  MINI_ROW_BORDER,
} from "@/components/chartist/common/MockupPrimitives";
import { TickerName } from "@/components/shared/TickerName";
import {
  WATCHLIST_SUMMARY,
  WATCHLIST_ITEMS,
  WATCHLIST_ALERTS,
  WATCHLIST_LOG,
} from "@/lib/chartist/mockData";

export function WatchlistView() {
  return (
    <div>
      <Breadcrumb trail={["Chartist", "관심종목 + 알람"]} />
      <PageHeader
        title="관심종목 + 알람"
        meta="개인 큐레이션 · 38 종목 · 알람 14개 활성"
      />
      <SummaryRow cells={WATCHLIST_SUMMARY} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-3">
        <Panel title="관심종목 리스트" subtitle="개인 메모 + 조건" bodyPad={false}>
          <table className={MINI_TABLE_CLS}>
            <thead>
              <tr>
                <th className={MINI_TH}>Ticker</th>
                <th className={MINI_TH}>태그</th>
                <th className={MINI_TH_NUM}>가격</th>
                <th className={MINI_TH_NUM}>Δ from Add</th>
                <th className={MINI_TH}>내 메모</th>
                <th className={MINI_TH}>Status</th>
              </tr>
            </thead>
            <tbody>
              {WATCHLIST_ITEMS.map((r) => (
                <tr key={r.name} style={MINI_ROW_BORDER}>
                  <td className={MINI_TD}>
                    <TickerName symbol="" name={r.name} />
                  </td>
                  <td className={MINI_TD}>
                    <span className="flex gap-1 flex-wrap">
                      {r.tags.map((t) => (
                        <Chip key={t} tone="accent">
                          {t}
                        </Chip>
                      ))}
                    </span>
                  </td>
                  <td className={MINI_TD_NUM}>{r.price.toLocaleString()}</td>
                  <td
                    className={MINI_TD_NUM}
                    style={{
                      color: r.from > 0 ? "var(--pos)" : "var(--neg)",
                    }}
                  >
                    {r.from > 0 ? "+" : ""}
                    {r.from.toFixed(1)}%
                  </td>
                  <td
                    className={`${MINI_TD} text-[10.5px] text-[color:var(--fg-muted)]`}
                  >
                    {r.memo}
                  </td>
                  <td className={MINI_TD}>
                    <Chip
                      tone={
                        r.tone === "pos"
                          ? "pos"
                          : r.tone === "neg"
                            ? "neg"
                            : r.tone === "amber"
                              ? "amber"
                              : "neutral"
                      }
                    >
                      {r.status}
                    </Chip>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel title="활성 알람" subtitle="조건 충족 시 트리거" bodyPad={false}>
          <table className={MINI_TABLE_CLS}>
            <thead>
              <tr>
                <th className={MINI_TH}>Ticker</th>
                <th className={MINI_TH}>조건</th>
                <th className={MINI_TH_NUM}>Target</th>
                <th className={MINI_TH_NUM}>현재</th>
                <th className={MINI_TH}>Status</th>
              </tr>
            </thead>
            <tbody>
              {WATCHLIST_ALERTS.map((r) => (
                <tr key={r.name + r.cond} style={MINI_ROW_BORDER}>
                  <td className={MINI_TD}>
                    <TickerName symbol="" name={r.name} />
                  </td>
                  <td className={`${MINI_TD} text-[11px]`}>{r.cond}</td>
                  <td className={MINI_TD_NUM}>
                    {typeof r.target === "number"
                      ? r.target.toLocaleString()
                      : (r.target ?? "—")}
                  </td>
                  <td className={MINI_TD_NUM}>
                    {typeof r.cur === "number"
                      ? r.cur.toLocaleString()
                      : (r.cur ?? "—")}
                  </td>
                  <td className={MINI_TD}>
                    <Chip
                      tone={
                        r.tone === "neg"
                          ? "neg"
                          : r.tone === "amber"
                            ? "amber"
                            : "neutral"
                      }
                    >
                      {r.status}
                    </Chip>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      </div>

      <Panel title="오늘 트리거된 알람" subtitle="타임스탬프 순" bodyPad={false}>
        <ActivityLog
          items={WATCHLIST_LOG.map((l) => ({
            time: l.time,
            tag: l.tag,
            tagClass: l.tagClass as "buy" | "sell" | "alert" | "sys",
            sym: l.sym,
            msg: l.msg,
          }))}
        />
      </Panel>
    </div>
  );
}
