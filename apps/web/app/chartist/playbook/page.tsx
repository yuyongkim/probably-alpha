// Chartist · Playbook — 12 체크리스트 + 준수율 통계.
import { PlaybookView } from "@/components/chartist/playbook/PlaybookView";

export const revalidate = 60;

export default function ChartistPlaybookPage() {
  return <PlaybookView />;
}
