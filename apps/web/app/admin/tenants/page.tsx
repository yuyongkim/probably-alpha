import { DensePage } from "@/components/shared/DensePage";
import { TenantTable } from "@/components/admin/TenantTable";

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <DensePage
      tab="Admin"
      current="테넌트"
      title="테넌트 관리 (B2B)"
      meta="owner_id 기반 · API key · 요금제 · rate limit"
    >
      <TenantTable />
    </DensePage>
  );
}
