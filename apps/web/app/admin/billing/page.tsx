import { DensePage } from "@/components/shared/DensePage";
import { UsageDashboard } from "@/components/admin/UsageDashboard";

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <DensePage
      tab="Admin"
      current="사용량"
      title="사용량 / 빌링"
      meta="API 호출수 · 평균 지연 · 예상 월요금"
    >
      <UsageDashboard />
    </DensePage>
  );
}
