// ROADMAP: KIS ELW 전용 TR (기초자산별 콜/풋, 내재변동성) 미연결.
//          Execute API 의 /quote /orderbook 은 주식만 지원.
import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="ELW" title="ELW (주식워런트)" meta="콜/풋 · 기초자산">
      <StubBlock
        icon="W"
        title="ELW 시세/주문 — KIS ELW TR 미연결"
        desc="KIS ELW 전용 엔드포인트 필요 (기초자산 스크리닝, 내재변동성, LP 스프레드). 현 시점 주식 쿼트 TR 로는 대체 불가."
        chips={["ROADMAP", "C: KIS TR 필요"]}
      />
    </DensePage>
  );
}
