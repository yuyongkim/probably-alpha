// StockDetailModal — global overlay rendered in root layout.
// Seven tabs, each pane dynamically imported to keep initial bundle small.
"use client";

import { useEffect } from "react";
import dynamic from "next/dynamic";
import {
  useStockModal,
  STOCK_MODAL_TABS,
  type StockModalTab,
} from "@/lib/stockModal";

// Lazy-load panes — keeps the modal shell tiny when closed.
const ChartPane = dynamic(
  () => import("./panes/ChartPane").then((m) => m.ChartPane),
  { ssr: false, loading: () => <PaneSkeleton /> },
);
const WizardViewsPane = dynamic(
  () => import("./panes/WizardViewsPane").then((m) => m.WizardViewsPane),
  { ssr: false, loading: () => <PaneSkeleton /> },
);
const FundamentalsPane = dynamic(
  () => import("./panes/FundamentalsPane").then((m) => m.FundamentalsPane),
  { ssr: false, loading: () => <PaneSkeleton /> },
);
const FlowPane = dynamic(
  () => import("./panes/FlowPane").then((m) => m.FlowPane),
  { ssr: false, loading: () => <PaneSkeleton /> },
);
const DartPane = dynamic(
  () => import("./panes/DartPane").then((m) => m.DartPane),
  { ssr: false, loading: () => <PaneSkeleton /> },
);
const NewsAIPane = dynamic(
  () => import("./panes/NewsAIPane").then((m) => m.NewsAIPane),
  { ssr: false, loading: () => <PaneSkeleton /> },
);
const NotesPane = dynamic(
  () => import("./panes/NotesPane").then((m) => m.NotesPane),
  { ssr: false, loading: () => <PaneSkeleton /> },
);

function PaneSkeleton() {
  return (
    <div className="text-[color:var(--fg-muted)] text-[11.5px]">
      Loading…
    </div>
  );
}

function renderPane(tab: StockModalTab, symbol: string) {
  switch (tab) {
    case "chart":        return <ChartPane symbol={symbol} />;
    case "wizards":      return <WizardViewsPane symbol={symbol} />;
    case "fundamentals": return <FundamentalsPane symbol={symbol} />;
    case "flow":         return <FlowPane symbol={symbol} />;
    case "dart":         return <DartPane symbol={symbol} />;
    case "news":         return <NewsAIPane symbol={symbol} />;
    case "notes":        return <NotesPane symbol={symbol} />;
  }
}

export function StockDetailModal() {
  const { open, ticker, tab, closeModal, setTab } = useStockModal();

  // ESC closes the modal.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeModal();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, closeModal]);

  if (!open || !ticker) return null;

  return (
    <div
      className="stock-modal-overlay"
      onClick={closeModal}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="stock-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <header
          className="flex items-center justify-between px-4 py-3 border-b"
          style={{ borderColor: "var(--border)" }}
        >
          <div className="flex items-baseline gap-3">
            <h2 className="display text-xl">{ticker.name}</h2>
            <span className="mono text-[11px] text-[color:var(--fg-muted)]">
              {ticker.symbol}
            </span>
            {ticker.sector && (
              <span className="chip accent">{ticker.sector}</span>
            )}
          </div>
          <button
            onClick={closeModal}
            className="text-[color:var(--fg-muted)] hover:text-[color:var(--fg)] text-sm"
            aria-label="Close"
          >
            ✕
          </button>
        </header>

        <nav className="stock-modal-tabs">
          {STOCK_MODAL_TABS.map((t) => (
            <button
              key={t.id}
              className={`stock-modal-tab ${t.id === tab ? "active" : ""}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>

        <div className="stock-modal-body">
          {renderPane(tab, ticker.symbol)}
        </div>
      </div>
    </div>
  );
}
