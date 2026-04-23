import { DensePage } from "@/components/shared/DensePage";
import { RagFilterSearch } from "@/components/research/RagFilterSearch";

export default function Page() {
  return (
    <DensePage
      tab="Research"
      current="Wizards 인터뷰"
      title="Market Wizards 인터뷰"
      meta="SCHWAGER 3부작 · Turtle · Livermore · LTCM · Soros"
    >
      <RagFilterSearch slug="interviews" initialQuery="cut losses" />
    </DensePage>
  );
}
