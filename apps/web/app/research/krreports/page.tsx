import { DensePage } from "@/components/shared/DensePage";
import { SummaryCards } from "@/components/shared/SummaryCards";
import { StubBlock } from "@/components/execute/StubBlock";
import { krreportsKpis } from "@/lib/research/mockData";

export default function Page() {
  return (
    <DensePage tab="Research" current="한국 증권사 리포트" title="국내 증권사 리포트 메타분석" meta="목표주가 · 투자의견 · 컨센서스">
      <SummaryCards cells={krreportsKpis} />
      <div style={{ marginTop: 14 }}>
        <StubBlock icon="⎗" title="증권사 리포트 PDF 자동 분석" desc="Dart_Analysis의 PDF 분석기 확장. 증권사 리포트 PDF → 목표가/근거/섹터 뷰 추출. 컨센서스 추적." />
      </div>
    </DensePage>
  );
}
