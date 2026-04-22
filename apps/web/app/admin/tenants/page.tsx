import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Admin" current="테넌트" title="테넌트 관리 (B2B)" meta="owner_id 기반">
      <StubBlock icon="T" title="B2B 고객 테넌트" desc="현재: 본인 1명(self). 확장 시: 각 고객별 스코프/쿼터/API 키/데이터 분리." />
    </DensePage>
  );
}
