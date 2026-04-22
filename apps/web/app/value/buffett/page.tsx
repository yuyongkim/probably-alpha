// Value · Buffett RAG — 버핏 지식베이스 (stub).

import { PageHeader } from "@/components/shared/PageHeader";
import { StubCard } from "@/components/shared/StubCard";

export default function ValueBuffettPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "버핏 지식베이스", current: true }]}
        title="버핏 RAG + 투자 서적"
        meta="54,934 CHUNKS"
      />
      <StubCard
        icon="B"
        title="버핏 서한 21년 + 148 PDF"
        desc='QuantPlatform의 투자 지식 RAG. TF-IDF 인덱스 54,934 청크. "XX 종목 상황에서 버핏은 뭐라 했을까?" 같은 질문 가능.'
        chips={["QuantPlatform 흡수"]}
      />
    </>
  );
}
