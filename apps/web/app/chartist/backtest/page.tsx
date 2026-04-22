// Chartist · Backtest — SEPA 전략 백테스트 (mock).
import {
  Breadcrumb,
  PageHeader,
  SummaryRow,
  Stub,
} from "@/components/chartist/common/MockupPrimitives";
import { BACKTEST_SUMMARY } from "@/lib/chartist/mockData";

export const revalidate = 60;

export default function ChartistBacktestPage() {
  return (
    <div>
      <Breadcrumb trail={["Chartist", "SEPA 백테스트"]} />
      <PageHeader title="SEPA 전략 백테스트" meta="LeaderSectorStock · v2.1" />
      <SummaryRow cells={BACKTEST_SUMMARY} />
      <div className="mt-4">
        <Stub
          icon="B"
          title="자산 곡선 + 거래 로그"
          desc="equity curve, drawdown, 월별 수익률 히트맵, 종목별 기여도, 진입/청산 사유 전체 공개."
        />
      </div>
    </div>
  );
}
