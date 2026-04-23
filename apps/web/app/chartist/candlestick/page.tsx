// Chartist · Candlestick — real ky.db scan via /api/v1/chartist/candlestick.
import { fetchEnvelope } from "@/lib/api";
import type { CandlestickResponse } from "@/types/chartist";
import { CandlestickView } from "@/components/chartist/candlestick/CandlestickView";

export const revalidate = 60;

export default async function ChartistCandlestickPage() {
  const data = await fetchEnvelope<CandlestickResponse>(
    "/api/v1/chartist/candlestick?limit=300",
  );
  return <CandlestickView data={data} />;
}
