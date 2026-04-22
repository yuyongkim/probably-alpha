// Admin · Status — Placeholder. Future: live status via /api/v1/admin/status.
export default function AdminStatusPage() {
  return (
    <div>
      <h1 className="display text-3xl mb-2">Platform Status</h1>
      <p className="text-sm text-[color:var(--fg-muted)] mb-6">
        서비스 · 토큰 · 시크릿 존재 여부 · 피처 플래그.
      </p>
      <div className="p-6 rounded-md border border-border bg-[color:var(--surface)]">
        <div className="text-[color:var(--accent)] text-xs uppercase tracking-widest mb-2">
          Coming in Phase 3
        </div>
        <p className="text-sm">
          <code className="mono">GET /api/v1/admin/status</code> 는 이미 동작. 이 페이지는 훅으로 연결 예정.
        </p>
      </div>
    </div>
  );
}
