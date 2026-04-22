import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";

const presets = [
  { name: "Moving Average Crossover", ret: "+14.2%", note: "3Y · MDD −18%" },
  { name: "RSI Mean Reversion", ret: "+8.7%", note: "3Y · Sharpe 0.94" },
  { name: "Bollinger Breakout", ret: "+19.3%", note: "3Y · MDD −22%" },
];

export default function Page() {
  return (
    <DensePage tab="Execute" current="KIS Backtester" title="KIS Backtester" meta="10 프리셋 · QuantConnect Lean 기반">
      <div className="grid-3">
        {presets.map((p) => (
          <div key={p.name} className="kv-card">
            <div className="kv-label">{p.name}</div>
            <div className="kv-value">{p.ret}</div>
            <div style={{ marginTop: 8, fontSize: 11.5, color: "var(--text-muted)" }}>{p.note}</div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 16 }}>
        <StubBlock icon="K" title="80 기술지표 + 파라미터 최적화" desc="KIS 샘플 레포의 backtester. Grid/Random Search, JSON/HTML 리포트. MCP 서버 포트 3846." chips={["KIS 흡수"]} />
      </div>
    </DensePage>
  );
}
