import { DensePage } from "@/components/shared/DensePage";
import { AIResearchPanel } from "@/components/research/AIResearchPanel";

export default function Page() {
  return (
    <DensePage
      tab="Research"
      current="AI Research Agent"
      title="AI Research Agent"
      meta="CLAUDE + RAG · ANTHROPIC_API_KEY 없으면 stub 모드"
    >
      <AIResearchPanel />
    </DensePage>
  );
}
