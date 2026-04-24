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
  // Native <button> — not <span role=button> — avoids the browser long-press /
  // accessibility "allow" hint that appears on non-native interactive elements.
  return (
    <button
      type="button"
      className={`ticker-name ${className ?? ""}`}
      onClick={() => openModal({ symbol, name, sector })}
    >
      {children ?? name}
    </button>
  );
}
