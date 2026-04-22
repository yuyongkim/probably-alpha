// Client-only mount point for the global stock detail modal.
// Exists because Next 15 disallows `dynamic(..., { ssr: false })`
// inside a server-component layout; this wrapper is a client boundary.
"use client";

import dynamic from "next/dynamic";

const StockDetailModal = dynamic(
  () =>
    import("@/components/shared/modals/StockDetailModal").then(
      (m) => m.StockDetailModal,
    ),
  { ssr: false },
);

export function StockDetailModalMount() {
  return <StockDetailModal />;
}
