// Chartist · Patterns — VCP / Base 패턴 (stub).
import {
  Breadcrumb,
  PageHeader,
  Stub,
} from "@/components/chartist/common/MockupPrimitives";

export const revalidate = 60;

export default function ChartistPatternsPage() {
  return (
    <div>
      <Breadcrumb trail={["Chartist", "VCP / Base 패턴"]} />
      <PageHeader
        title="VCP / Base 패턴 탐지"
        meta="Minervini Stage 분류"
      />
      <Stub
        icon="V"
        title="패턴 갤러리"
        desc="VCP 3단계 수축, 핸들 있는 컵, 평탄 베이스, 상승 삼각형. 각 종목 미니 차트 + 돌파 대기 알림 등록."
        chips={["VCP 1단계", "VCP 2단계", "VCP 3단계", "Cup & Handle", "Flat Base"]}
      />
    </div>
  );
}
