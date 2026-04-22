import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="리스크 / 증거금" title="리스크 관리" meta="VAR · 증거금 · 섹터 집중도">
      <StubBlock icon="R" title="전체 리스크 대시보드" desc="계좌 전체 VaR, 섹터/종목 집중도, 상관관계 행렬, 증거금 사용률." />
    </DensePage>
  );
}
