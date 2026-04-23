import { DensePage } from "@/components/shared/DensePage";
import { RagFilterSearch } from "@/components/research/RagFilterSearch";

export default function Page() {
  return (
    <DensePage
      tab="Research"
      current="블로그 아카이브"
      title="투자 블로그 아카이브"
      meta="TISTORY · NAVER · SUBSTACK — 크롤러 대기"
    >
      <RagFilterSearch
        slug="blogs"
        emptyCopy="현재 블로그 코퍼스는 비어 있습니다. QuantPlatform Tistory 크롤러를 연결한 뒤 RAG 인덱스를 재빌드하면 같은 검색창이 바로 동작합니다."
      />
    </DensePage>
  );
}
