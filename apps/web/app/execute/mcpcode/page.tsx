import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="MCP — Code Assistant" title="KIS Code Assistant MCP" meta="자연어 → KIS API 코드">
      <StubBlock icon="{ }" title="코드 자동 검색/생성" desc='"해외주식 미체결 정정 주문 코드" 같은 자연어로 KIS 샘플에서 정확한 호출 코드 검색. 자동 주석 포함.' chips={["KIS MCP"]} />
    </DensePage>
  );
}
