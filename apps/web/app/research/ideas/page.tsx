import { DensePage } from "@/components/shared/DensePage";
import { LocalStorageList } from "@/components/research/LocalStorageList";

export default function Page() {
  return (
    <DensePage
      tab="Research"
      current="아이디어 랩"
      title="전략 아이디어 랩"
      meta="BRAINSTORM · localStorage 기반 · 브라우저에만 저장"
    >
      <LocalStorageList
        storageKey="ky:research:ideas"
        title="idea"
        emptyCopy="아직 저장된 아이디어가 없습니다. 관찰 → 가설 → 검증 플랜 순으로 적어두세요."
        fields={[
          { name: "title", label: "제목", placeholder: "예: 외인 5일 연속 순매수 + Stage 2" },
          {
            name: "tags",
            label: "태그",
            placeholder: "momentum, korea, microcap",
          },
          {
            name: "hypothesis",
            label: "가설",
            placeholder: "왜 이 아이디어가 유효할 것으로 보는가?",
            type: "textarea",
          },
          {
            name: "test_plan",
            label: "검증 플랜",
            placeholder: "어떤 기간/유니버스로 간이 백테스트할지",
            type: "textarea",
          },
        ]}
      />
    </DensePage>
  );
}
