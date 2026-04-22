// Click-to-open-modal ticker label.
// Replaces the mockup's bare `.ticker-name` span everywhere a stock is listed.
"use client";

import { useStockModal } from "@/lib/stockModal";
import type { TickerRef } from "@/types/chartist";

interface Props extends TickerRef {
  className?: string;
  children?: React.ReactNode;
}

export function TickerName({ symbol, name, sector, className, children }: Props) {
  const openModal = useStockModal((s) => s.openModal);
  return (
    <span
      className={`ticker-name ${className ?? ""}`}
      onClick={() => openModal({ symbol, name, sector })}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          openModal({ symbol, name, sector });
        }
      }}
      role="button"
      tabIndex={0}
    >
      {children ?? name}
    </span>
  );
}
