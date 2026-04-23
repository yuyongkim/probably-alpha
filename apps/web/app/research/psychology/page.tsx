import { DensePage } from "@/components/shared/DensePage";
import { RagFilterSearch } from "@/components/research/RagFilterSearch";

export default function Page() {
  return (
    <DensePage
      tab="Research"
      current="트레이딩 심리"
      title="Trading Psychology Library"
      meta="ELDER · DOUGLAS · KAHNEMAN · SHILLER"
    >
      <div className="quote-strip">
        &ldquo;The market is a device for transferring money from the impatient to the
        patient.&rdquo; <span className="attr">— Warren Buffett</span>
      </div>
      <RagFilterSearch slug="psychology" initialQuery="discipline" />
    </DensePage>
  );
}
