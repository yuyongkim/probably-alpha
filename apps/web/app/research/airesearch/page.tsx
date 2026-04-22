import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Research" current="AI Research Agent" title="AI Research Agent" meta="CLAUDE · 자동 리포트 생성">
      <StubBlock icon="⟲" title="질문 → 자동 종합 리포트" desc='"반도체 섹터 이번 분기 전망" 같은 질문 → Claude가 DART+뉴스+재무+차트 전부 조합해 리포트. PDF 다운로드.' chips={["MCP 통합"]} />
    </DensePage>
  );
}
