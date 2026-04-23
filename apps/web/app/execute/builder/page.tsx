// ROADMAP: 비주얼 Strategy Builder는 전용 백엔드 필요 (indicator registry,
//          YAML 직렬화, live signal 엔진). 현재 ky_core.backtest 엔진은
//          코드 기반 전략만 지원하며 드래그앤드롭 DSL 미구현.
//          See packages/core/ky_core/backtest/strategies/ for current surface.
import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage
      tab="Execute"
      current="Strategy Builder"
      title="비주얼 Strategy Builder"
      meta="80 지표 · 57 캔들스틱 패턴 · AND/OR"
    >
      <StubBlock
        icon="W"
        title="드래그앤드롭 전략 설계 — 백엔드 미구축"
        desc="Indicator registry · YAML 직렬화 · 라이브 시그널 엔진 전부 신규 백엔드 필요. 현재는 ky_core.backtest 의 코드 기반 전략(REGISTRY)만 지원."
        chips={["ROADMAP", "B: 신규 백엔드"]}
      />
    </DensePage>
  );
}
