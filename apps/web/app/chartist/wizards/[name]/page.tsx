// Chartist · Wizards · [name] — dynamic per-wizard page.
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
  const detail = await fetchEnvelope<WizardDetail>(
    `/api/v1/chartist/wizards/${name}?limit=200`
  );
  return <WizardPage detail={detail} config={config} />;
}
