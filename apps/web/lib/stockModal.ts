// Global stock detail modal store.
// Zustand is the smallest x-tree state lib that also works inside
// Next 15 server/client boundary (we only touch it from client components).
"use client";

import { create } from "zustand";
import type { TickerRef } from "@/types/chartist";

export type StockModalTab =
  | "chart"
  | "wizards"
  | "fundamentals"
  | "flow"
  | "dart"
  | "news"
  | "notes";

export const STOCK_MODAL_TABS: { id: StockModalTab; label: string }[] = [
  { id: "chart", label: "Chart" },
  { id: "wizards", label: "Wizard Views" },
  { id: "fundamentals", label: "Fundamentals" },
  { id: "flow", label: "수급" },
  { id: "dart", label: "공시" },
  { id: "news", label: "News & AI" },
  { id: "notes", label: "My Notes" },
];

interface StockModalState {
  open: boolean;
  ticker: TickerRef | null;
  tab: StockModalTab;
  openModal: (ref: TickerRef) => void;
  closeModal: () => void;
  setTab: (tab: StockModalTab) => void;
}

export const useStockModal = create<StockModalState>((set) => ({
  open: false,
  ticker: null,
  tab: "chart",
  openModal: (ref) => set({ open: true, ticker: ref, tab: "chart" }),
  closeModal: () => set({ open: false }),
  setTab: (tab) => set({ tab }),
}));
