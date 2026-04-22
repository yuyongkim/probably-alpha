// FooterStrip — bottom bar with 7-adapter health dots.
// Server component: fetches /api/v1/admin/data_health at render.
// Fails quietly → renders a neutral "unknown" strip so shell stays intact.
import { fetchEnvelope } from "@/lib/api";

interface AdapterHealth {
  source_id: string;
  ok?: boolean;
  configured?: boolean;
  last_error?: string;
}
interface DataHealth {
  adapters: AdapterHealth[];
}

const ADAPTER_LABELS: Record<string, string> = {
  kis: "KIS",
  dart: "DART",
  fred: "FRED",
  ecos: "ECOS",
  eia: "EIA",
  exim: "EXIM",
  kosis: "KOSIS",
  kiwoom: "Kiwoom",
  naver: "Naver",
};

export async function FooterStrip() {
  let adapters: AdapterHealth[] = [];
  try {
    const data = await fetchEnvelope<DataHealth>("/api/v1/admin/data_health", {
      revalidate: 120,
    });
    adapters = data.adapters ?? [];
  } catch {
    // Degrade gracefully — emit a ghost strip.
    adapters = Object.keys(ADAPTER_LABELS).slice(0, 7).map((k) => ({
      source_id: k,
      ok: false,
      configured: false,
    }));
  }
  const today = new Date().toISOString().slice(0, 10);
  return (
    <footer className="footer-strip">
      <div className="data-health">
        {adapters.map((a) => {
          const label = ADAPTER_LABELS[a.source_id] ?? a.source_id.toUpperCase();
          const healthy = a.ok === true;
          return (
            <span key={a.source_id}>
              <span className={`health-dot${healthy ? "" : " off"}`} />
              {label}
            </span>
          );
        })}
      </div>
      <div>© Probably Alpha · {today} · build dev</div>
    </footer>
  );
}
