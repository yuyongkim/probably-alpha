// ROADMAP: ETF 유니버스/NAV/괴리율 API 미구축. 개별 ETF quote 는
//          /api/v1/execute/quote/{symbol} 로 조회 가능하나 전용 리스트
//          및 추종오차 계산 엔드포인트 필요.
import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="ETF / ETN" title="ETF / ETN" meta="국내 · 해외">
      <StubBlock
        icon="E"
        title="ETF 포트폴리오 — 전용 API 미구축"
        desc="테마별 ETF 리스트, NAV/iNAV 스트림, 추종오차 계산 신규 백엔드 필요. 개별 ETF 현재가만 /execute/quote 로 조회 가능."
        chips={["ROADMAP", "B: 신규 백엔드"]}
      />
    </DensePage>
  );
}
