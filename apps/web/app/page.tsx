"use client";

import { useEffect, useState } from "react";

import { BreakoutsList } from "@/components/home/BreakoutsList";
import { HeroHeader } from "@/components/home/HeroHeader";
import { HomeFooter } from "@/components/home/HomeFooter";
import { EmptyRow, ErrorRow, Panel } from "@/components/home/Panel";
import { PillCard } from "@/components/home/PillCard";
import { StagesList } from "@/components/home/StagesList";
import { TabDirectory } from "@/components/home/TabDirectory";
import { TopLeadersList } from "@/components/home/TopLeadersList";
import { TopSectorsList } from "@/components/home/TopSectorsList";
import { WizardsList } from "@/components/home/WizardsList";
import type { TodayBundle } from "@/types/today";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:31300";

export default function HomePage() {
  const [bundle, setBundle] = useState<TodayBundle | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/api/v1/chartist/today`)
      .then((r) => r.json())
      .then((body) => {
        if (cancelled) return;
        if (body?.ok && body.data) setBundle(body.data as TodayBundle);
        else setErr(body?.error?.message ?? "no data");
      })
      .catch((e) => {
        if (!cancelled) setErr(String(e?.message ?? e));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="max-w-6xl">
      <HeroHeader asOf={bundle?.date} />

      {bundle && bundle.market.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
          {bundle.market.map((p) => (
            <PillCard key={p.label} pill={p} />
          ))}
        </div>
      )}
      {bundle && bundle.summary.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mb-6">
          {bundle.summary.map((p) => (
            <PillCard key={p.label} pill={p} compact />
          ))}
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-4 mb-6">
        <Panel title="Top Sectors (오늘)" href="/chartist/sectors">
          {err ? (
            <ErrorRow msg={err} />
          ) : bundle && bundle.sectors.length > 0 ? (
            <TopSectorsList rows={bundle.sectors} />
          ) : (
            <EmptyRow />
          )}
        </Panel>
        <Panel title="Top Leaders (오늘)" href="/chartist/leaders">
          {err ? (
            <ErrorRow msg={err} />
          ) : bundle && bundle.leaders.length > 0 ? (
            <TopLeadersList rows={bundle.leaders} />
          ) : (
            <EmptyRow />
          )}
        </Panel>
      </div>

      <div className="grid md:grid-cols-3 gap-4 mb-6">
        <Panel title="Wizards Pass" href="/chartist/wizards">
          {bundle?.wizards_pass?.length ? (
            <WizardsList rows={bundle.wizards_pass} />
          ) : (
            <EmptyRow />
          )}
        </Panel>
        <Panel title="Breakouts" href="/chartist/breakouts/52w">
          {bundle?.breakouts?.length ? (
            <BreakoutsList rows={bundle.breakouts} />
          ) : (
            <EmptyRow />
          )}
        </Panel>
        <Panel title="Stage Distribution" href="/chartist/wizards/minervini">
          {bundle?.stage_dist?.length ? (
            <StagesList rows={bundle.stage_dist} />
          ) : (
            <EmptyRow />
          )}
        </Panel>
      </div>

      <TabDirectory />
      <HomeFooter universeSize={bundle?.universe_size} />
    </div>
  );
}
