// ROADMAP: 리스크/증거금 대시보드 백엔드 미구축. 계좌 VaR, 섹터 집중도,
//          상관행렬, 증거금 사용률 계산 엔드포인트 신규 필요.
//          전제조건: /execute/overview 가 positions 를 실데이터로 반환해야 함.
import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage
      tab="Execute"
      current="리스크 / 증거금"
      title="리스크 관리"
      meta="VaR · 증거금 · 섹터 집중도"
    >
      <StubBlock
        icon="R"
        title="리스크 대시보드 — 계산 엔진 미구축"
        desc="VaR/CVaR, 섹터·종목 집중도, 상관행렬, 증거금 사용률 계산 신규 백엔드 필요. 선결조건: inquire-balance TR 로 실제 포지션 확보."
        chips={["ROADMAP", "B: 신규 백엔드"]}
      />
    </DensePage>
  );
}
