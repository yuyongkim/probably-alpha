// Value · 리포트 분석기 — 증권사 PDF 구조화 (stub).

import { PageHeader } from "@/components/shared/PageHeader";
import { StubCard } from "@/components/shared/StubCard";

export default function ValueReportsPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "리포트 분석기", current: true }]}
        title="증권사 리포트 PDF 분석"
        meta="요약 · 목표주가 · 의견"
      />
      <StubCard
        icon="R"
        title="PDF → 구조화"
        desc="증권사 리포트 PDF를 자동 파싱. 목표주가 히스토리, 컨센서스 변화 추적."
      />
    </>
  );
}
