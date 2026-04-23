import { DensePage } from "@/components/shared/DensePage";
import { AuditLog } from "@/components/admin/AuditLog";

export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <DensePage
      tab="Admin"
      current="감사 로그"
      title="감사 로그"
      meta="tenant_created · key_rotated · tenant_disabled · order_placed"
    >
      <AuditLog />
    </DensePage>
  );
}
