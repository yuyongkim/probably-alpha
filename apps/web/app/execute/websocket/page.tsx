// Execute · WebSocket — KIS OAuth status + planned subscription roadmap.
// Real WebSocket streaming (approval_key + ws://ops.koreainvestment.com:21000)
// lands in a follow-up phase once the OAuth backbone is stable.
import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
import { SummaryCards } from "@/components/shared/SummaryCards";
import { fetchEnvelope } from "@/lib/api";

export const revalidate = 60;

interface HealthData {
  ok: boolean;
  source_id: string;
  latency_ms: number | null;
  last_error: string | null;
  token_cached?: boolean;
  base_url?: string;
  env?: string;
}

async function loadHealth(): Promise<HealthData | null> {
  try {
    return await fetchEnvelope<HealthData>("/api/v1/execute/health", {
      revalidate: 30,
    });
  } catch {
    return null;
  }
}

export default async function Page() {
  const h = await loadHealth();
  const tokenOk = h?.ok === true;

  const cells = [
    {
      label: "OAuth Status",
      value: tokenOk ? "OK" : "FAIL",
      delta: tokenOk ? "token cached · 23h TTL" : h?.last_error ?? "no response",
      tone: (tokenOk ? "pos" : "neg") as "pos" | "neg",
    },
    {
      label: "REST Latency",
      value: h?.latency_ms != null ? `${h.latency_ms.toFixed(0)}ms` : "—",
      delta: "tokenP",
      tone: (h?.latency_ms != null && h.latency_ms < 500 ? "pos" : undefined) as "pos" | undefined,
    },
    {
      label: "WebSocket URL",
      value: "ops:21000",
      delta: "ws://ops.koreainvestment.com",
    },
    {
      label: "Env",
      value: h?.env ?? "real",
      delta: h?.base_url?.replace(/^https?:\/\//, "") ?? "",
    },
  ];

  return (
    <DensePage
      tab="Execute"
      current="WebSocket 실시간"
      title="KIS WebSocket 실시간 시세"
      meta={tokenOk ? "OAuth OK · 구독 준비됨" : "OAuth FAIL · 연결 대기"}
    >
      <SummaryCards cells={cells} />
      <div style={{ marginTop: 20 }}>
        <StubBlock
          icon={tokenOk ? "OK" : "WAIT"}
          title={tokenOk ? "KIS WebSocket 구독 준비 완료" : "KIS WebSocket 연결 대기"}
          desc={
            tokenOk
              ? "OAuth 토큰 확보. 다음 단계: /oauth2/Approval 로 approval_key 발급 → ws://ops.koreainvestment.com:21000 구독 → 국내/해외 실시간 호가/체결 스트림."
              : h?.last_error ?? "OAuth 토큰을 먼저 확보해야 WebSocket 구독이 가능합니다."
          }
        />
      </div>
    </DensePage>
  );
}
