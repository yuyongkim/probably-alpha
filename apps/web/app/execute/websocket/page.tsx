import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
import { SummaryCards } from "@/components/shared/SummaryCards";

export default function Page() {
  return (
    <DensePage tab="Execute" current="WebSocket 실시간" title="KIS WebSocket 실시간 시세" meta="ops.koreainvestment.com:21000">
      <SummaryCards cells={[
        { label: "Subscribed", value: "47", delta: "국내 38 · 해외 9", tone: "pos" },
        { label: "Latency", value: "12ms", delta: "p95", tone: "pos" },
        { label: "Messages/s", value: "284", delta: "peak 1,240" },
        { label: "Uptime", value: "99.98%", delta: "24h", tone: "pos" },
      ]} />
      <div style={{ marginTop: 20 }}>
        <StubBlock icon="⚡" title="실시간 호가/체결 스트림" desc="국내주식/채권/선옵/해외주식 전체 WebSocket. 라이브 차트, 호가창, 돌파 알림 엔진 기반." />
      </div>
    </DensePage>
  );
}
