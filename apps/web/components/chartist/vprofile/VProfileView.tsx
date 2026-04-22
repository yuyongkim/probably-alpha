import {
  Breadcrumb,
  PageHeader,
  SummaryRow,
  Panel,
  Chip,
  MINI_TABLE_CLS,
  MINI_TH,
  MINI_TH_NUM,
  MINI_TD,
  MINI_TD_NUM,
  MINI_ROW_BORDER,
} from "@/components/chartist/common/MockupPrimitives";
import { TickerName } from "@/components/shared/TickerName";
import { VPROFILE_SUMMARY, VPROFILE_ROWS } from "@/lib/chartist/mockData";

export function VProfileView() {
  return (
    <div>
      <Breadcrumb trail={["Chartist", "Volume Profile"]} />
      <PageHeader
        title="Volume Profile (VPVR)"
        meta="POC · VAH · VAL · HIGH VOLUME NODE"
      />
      <SummaryRow cells={VPROFILE_SUMMARY} />

      <Panel title="VPVR 상태별 종목" subtitle="POC / VAH / VAL 위치" bodyPad={false}>
        <table className={MINI_TABLE_CLS}>
          <thead>
            <tr>
              <th className={MINI_TH}>Ticker</th>
              <th className={MINI_TH_NUM}>Price</th>
              <th className={MINI_TH_NUM}>POC</th>
              <th className={MINI_TH_NUM}>VAH</th>
              <th className={MINI_TH_NUM}>VAL</th>
              <th className={MINI_TH}>Position</th>
              <th className={MINI_TH}>Signal</th>
            </tr>
          </thead>
          <tbody>
            {VPROFILE_ROWS.map((r) => (
              <tr key={r.name} style={MINI_ROW_BORDER}>
                <td className={MINI_TD}>
                  <TickerName symbol="" name={r.name} />
                </td>
                <td className={MINI_TD_NUM}>{r.price.toLocaleString()}</td>
                <td className={MINI_TD_NUM}>{r.poc.toLocaleString()}</td>
                <td className={MINI_TD_NUM}>{r.vah.toLocaleString()}</td>
                <td className={MINI_TD_NUM}>{r.val.toLocaleString()}</td>
                <td className={MINI_TD}>
                  <Chip
                    tone={
                      r.tone === "pos"
                        ? "pos"
                        : r.tone === "neg"
                          ? "neg"
                          : "amber"
                    }
                  >
                    {r.pos}
                  </Chip>
                </td>
                <td className={MINI_TD}>
                  <Chip
                    tone={
                      r.tone === "pos"
                        ? "pos"
                        : r.tone === "neg"
                          ? "neg"
                          : "neutral"
                    }
                  >
                    {r.signal}
                  </Chip>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}
