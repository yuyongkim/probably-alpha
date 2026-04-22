// Execute · MCP Trading — dense mock (12 scenarios + activity + 10 safety rails + Ask Claude).
import { DensePage } from "@/components/shared/DensePage";
import { SummaryCards } from "@/components/shared/SummaryCards";
import { McpScenarios } from "@/components/execute/McpScenarios";
import { ActivityLogBlock } from "@/components/execute/ActivityLogBlock";
import { SafetyRailsList } from "@/components/execute/SafetyRailsList";
import { AskClaudePanel } from "@/components/execute/AskClaudePanel";
import {
  mcpActivity, mcpAskExamples, mcpTradeKpis, safetyRails, scenarios,
} from "@/lib/execute/mockData";

export default function Page() {
  return (
    <DensePage tab="Execute" current="MCP — Trading" title="KIS Trading MCP · 대화형 주문" meta="CLAUDE + KIS OAUTH · 내 계좌 직접 실행 · SAFETY RAILS">
      <div className="quote-strip">&ldquo;The future of trading UI is not screens. It&apos;s conversation.&rdquo; <span className="attr">— AI-first Platform Principle</span></div>
      <SummaryCards cells={mcpTradeKpis} />
      <div className="grid-2" style={{ marginBottom: 10 }}>
        <div className="panel">
          <div className="panel-header"><h2>시나리오 템플릿</h2><span className="muted">검증된 주문 패턴 12종</span></div>
          <div className="panel-body p0"><McpScenarios rows={scenarios} /></div>
        </div>
        <div className="panel">
          <div className="panel-header"><h2>오늘 AI 대화 로그</h2><span className="muted">실행된 / 거부된 주문</span></div>
          <div className="panel-body p0"><ActivityLogBlock items={mcpActivity} /></div>
        </div>
      </div>
      <div className="grid-2">
        <div className="panel">
          <div className="panel-header"><h2>Safety Rails</h2><span className="muted">AI 주문 안전장치</span></div>
          <div className="panel-body">
            <SafetyRailsList rails={safetyRails} />
            <div style={{ marginTop: 12, padding: "10px 12px", background: "var(--neg-soft)", borderRadius: 6, fontSize: 11, color: "var(--text)", lineHeight: 1.5 }}>
              <strong style={{ color: "var(--neg)" }}>Kill Switch:</strong>{" "}
              <code>MCP_TRADING_ENABLED=0</code>{" "}
              설정 시 즉시 모든 AI 주문 차단. 웹소켓 주문도 동시에 차단됨.
            </div>
          </div>
        </div>
        <AskClaudePanel
          title="Ask Claude · 대화 시작"
          desc="내 계좌 + 시세 + 전략 + 신호 전부 보며 답하고, 승인 시 실제 주문 실행. OAuth 기반 보안."
          examples={mcpAskExamples}
        />
      </div>
    </DensePage>
  );
}
