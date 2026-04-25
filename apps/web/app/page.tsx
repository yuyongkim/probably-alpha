"use client";

import { useEffect, useState } from "react";

import { BreakoutsList } from "@/components/home/BreakoutsList";
import { DataSourcesBar } from "@/components/home/DataSourcesBar";
import { HeroSection } from "@/components/home/HeroSection";
import { HomeFooter } from "@/components/home/HomeFooter";
import { EmptyRow, ErrorRow, Panel } from "@/components/home/Panel";
import { PillCard } from "@/components/home/PillCard";
import { SampleQueries } from "@/components/home/SampleQueries";
import { StagesList } from "@/components/home/StagesList";
import { TabDirectory } from "@/components/home/TabDirectory";
import { TopLeadersList } from "@/components/home/TopLeadersList";
import { TopSectorsList } from "@/components/home/TopSectorsList";
import { ValueProposition } from "@/components/home/ValueProposition";
import { WizardsList } from "@/components/home/WizardsList";
import { apiBase } from "@/lib/apiBase";
import type { TodayBundle } from "@/types/today";

export default function HomePage() {
  const [bundle, setBundle] = useState<TodayBundle | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${apiBase()}/api/v1/chartist/today`)
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
    <div className="w-full">
      {/* Hero — who + what + primary actions + live snapshot */}
      <HeroSection
        asOf={bundle?.date}
        universeSize={bundle?.universe_size}
        bundle={bundle}
      />

      {/* What the platform does — 3-lens explainer */}
      <ValueProposition />

      {/* Today's live data — market + summary pills */}
      {bundle && (bundle.market.length > 0 || bundle.summary.length > 0) && (
        <section className="mb-10">
          <div className="flex items-baseline justify-between mb-4 flex-wrap gap-2">
            <h2 className="display text-xl">오늘의 시장</h2>
            <span className="mono text-[10.5px] text-[color:var(--fg-muted)]">
              LIVE · as-of {bundle.date}
            </span>
          </div>
          {bundle.market.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-2">
              {bundle.market.map((p) => (
                <PillCard key={p.label} pill={p} />
              ))}
            </div>
          )}
          {bundle.summary.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {bundle.summary.map((p) => (
                <PillCard key={p.label} pill={p} compact />
              ))}
            </div>
          )}
        </section>
      )}

      {/* Today's picks — sectors + leaders side by side */}
      <section className="mb-10">
        <div className="flex items-baseline justify-between mb-4 flex-wrap gap-2">
          <h2 className="display text-xl">오늘의 주도주 · 섹터</h2>
          <span className="mono text-[10.5px] text-[color:var(--fg-muted)]">
            LEADER · ROTATION
          </span>
        </div>
        <div className="grid md:grid-cols-2 gap-3">
          <Panel title="Top Sectors" href="/chartist/sectors">
            {err ? (
              <ErrorRow msg={err} />
            ) : bundle && bundle.sectors.length > 0 ? (
              <TopSectorsList rows={bundle.sectors} />
            ) : (
              <EmptyRow />
            )}
          </Panel>
          <Panel title="Top Leaders" href="/chartist/leaders">
            {err ? (
              <ErrorRow msg={err} />
            ) : bundle && bundle.leaders.length > 0 ? (
              <TopLeadersList rows={bundle.leaders} />
            ) : (
              <EmptyRow />
            )}
          </Panel>
        </div>
      </section>

      {/* Scanners — wizards / breakouts / stage dist */}
      <section className="mb-10">
        <div className="flex items-baseline justify-between mb-4 flex-wrap gap-2">
          <h2 className="display text-xl">오늘의 스캐너</h2>
          <span className="mono text-[10.5px] text-[color:var(--fg-muted)]">
            WIZARDS · BREAKOUTS · STAGES
          </span>
        </div>
        <div className="grid md:grid-cols-3 gap-3">
          <Panel title="Wizards Pass" href="/chartist/wizards">
            {bundle?.wizards_pass?.length ? (
              <WizardsList rows={bundle.wizards_pass} />
            ) : (
              <EmptyRow />
            )}
          </Panel>
          <Panel title="52주 돌파" href="/chartist/breakouts/52w">
            {bundle?.breakouts?.length ? (
              <BreakoutsList rows={bundle.breakouts} />
            ) : (
              <EmptyRow />
            )}
          </Panel>
          <Panel title="Minervini Stages" href="/chartist/wizards/minervini">
            {bundle?.stage_dist?.length ? (
              <StagesList rows={bundle.stage_dist} />
            ) : (
              <EmptyRow />
            )}
          </Panel>
        </div>
      </section>

      {/* AI research — canned sample queries */}
      <SampleQueries />

      {/* Data provenance — trust bar */}
      <DataSourcesBar />

      {/* 6-tab directory */}
      <TabDirectory />

      <HomeFooter universeSize={bundle?.universe_size} />
    </div>
  );
}
