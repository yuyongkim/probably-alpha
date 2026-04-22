// Chartist · Support/Resistance — 지지/저항 자동감지 (stub).
import {
  Breadcrumb,
  PageHeader,
  Stub,
} from "@/components/chartist/common/MockupPrimitives";

export const revalidate = 60;

export default function ChartistSupportPage() {
  return (
    <div>
      <Breadcrumb trail={["Chartist", "지지/저항 자동감지"]} />
      <PageHeader
        title="지지/저항 자동감지"
        meta="PIVOT · 장기 고점/저점 · 5% 중복 제거"
      />
      <Stub
        icon="⇵"
        title="피벗포인트 + 장기 분석"
        desc="QuantPlatform의 지지/저항 엔진. 각 종목별 15개 기술지표와 함께 주요 지지/저항 선 자동 추출. 돌파·이탈 알림 연결."
        chips={["QuantPlatform 흡수"]}
      />
    </div>
  );
}
