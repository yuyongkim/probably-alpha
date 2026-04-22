// Chartist · Wizards · [name] — dynamic per-wizard page.
// Falls back gracefully to a synthetic `detail` when the API is
// unavailable, so the mockup-density preview still renders.
import { notFound } from "next/navigation";
import { fetchEnvelope } from "@/lib/api";
import type { WizardDetail } from "@/types/chartist";
import { getWizardConfig } from "@/lib/wizards";
import { WizardPage } from "@/components/chartist/wizards/WizardPage";

export const revalidate = 60;

interface Props {
  params: Promise<{ name: string }>;
}

export default async function ChartistWizardDetailPage({ params }: Props) {
  const { name } = await params;
  const config = getWizardConfig(name);
  if (!config) notFound();

  let detail: WizardDetail;
  try {
    detail = await fetchEnvelope<WizardDetail>(
      `/api/v1/chartist/wizards/${name}?limit=200`,
    );
  } catch {
    // API unavailable → render mock-only version.
    detail = {
      as_of: new Date().toISOString().slice(0, 10).replaceAll("-", ""),
      key: name,
      name: config.name,
      condition: config.rules.join(" · "),
      count: 0,
      rows: [],
    };
  }

  return <WizardPage detail={detail} config={config} />;
}
