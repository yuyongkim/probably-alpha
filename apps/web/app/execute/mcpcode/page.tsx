// ROADMAP: KIS Code Assistant MCP 는 별도 MCP 서버 필요 (자연어→코드 검색/
//          생성, KIS 샘플 레포 임베딩). 현재 백엔드는 주식 시세/SSE 만 노출.
//          See apps/api/routers/assistant/ — 현재는 LLM chat 만 지원.
import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage
      tab="Execute"
      current="MCP — Code Assistant"
      title="KIS Code Assistant MCP"
      meta="자연어 → KIS API 코드"
    >
      <StubBlock
        icon="{ }"
        title="코드 자동 검색/생성 — MCP 서버 미구축"
        desc="KIS 샘플 레포 임베딩 + code-aware 검색 엔드포인트 신규 개발 필요. /api/v1/assistant 는 현재 범용 chat 만 지원."
        chips={["ROADMAP", "B: 신규 백엔드"]}
      />
    </DensePage>
  );
}
