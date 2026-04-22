import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Research" current="블로그 아카이브" title="투자 블로그 아카이브" meta="Tistory 자동 크롤링">
      <StubBlock icon="✎" title="관심 블로거 자동 수집" desc="QuantPlatform의 Tistory 크롤러. 체크포인트 지원. 마크다운 저장 → RAG 인덱스." chips={["QuantPlatform 흡수"]} />
    </DensePage>
  );
}
