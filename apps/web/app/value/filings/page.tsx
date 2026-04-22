// Value · Filings — 사업보고서 PDF 분석 (stub).

import { PageHeader } from "@/components/shared/PageHeader";
import { StubCard } from "@/components/shared/StubCard";

export default function ValueFilingsPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "사업보고서 PDF", current: true }]}
        title="사업보고서 심층 분석"
        meta="DART PDF · 섹션별 추출"
      />
      <StubCard
        icon="F"
        title="DART PDF 어시스턴트"
        desc="500페이지짜리 사업보고서에서 사업부문 매출/수익성/리스크 섹션만 추출. LLM 요약."
      />
    </>
  );
}
