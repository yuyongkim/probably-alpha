// ROADMAP: 해외 선물옵션 (CME/EUREX/HKEX) TR 미연결. Execute API 의
//          시세 계열은 국내주식(market="J") 전용.
import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage
      tab="Execute"
      current="해외 선물옵션"
      title="해외 선물옵션"
      meta="CME · EUREX · HKEX"
    >
      <StubBlock
        icon="F°"
        title="해외 선옵 — KIS 해외파생 TR 미연결"
        desc="CME 원유/금/S&P500, EUREX, HKEX 각 시장별 TR 필요. 현재 Execute API 는 국내주식만 지원."
        chips={["ROADMAP", "C: KIS TR 필요"]}
      />
    </DensePage>
  );
}
