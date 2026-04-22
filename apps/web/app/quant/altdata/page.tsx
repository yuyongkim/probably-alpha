// Quant · Alternative Data — stub (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { StubCard } from "@/components/shared/StubCard";

export default function AltDataPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "Alternative Data", current: true }]}
        title="Alternative Data"
        meta="카드매출 · 웹트래픽 · 위성 · 뉴스 · 소셜"
      />
      <StubCard
        icon="◈"
        title="대체 데이터 신호"
        desc="신한카드 업종별 매출 지수, 모바일인덱스 앱 DAU, 네이버 검색 트렌드, 뉴스 감성. 전통 재무 보완."
        chips={["신한카드", "모바일인덱스", "Naver Datalab", "뉴스 감성"]}
      />
    </>
  );
}
