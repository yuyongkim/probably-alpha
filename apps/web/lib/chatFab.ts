// Zustand store for the floating chat panel.
// Small and purpose-built; kept separate from useStockModal to avoid
// conflating "open a stock detail" with "open the assistant chat".
"use client";

import { create } from "zustand";

interface ChatFabState {
  open: boolean;
  openPanel: () => void;
  closePanel: () => void;
  toggle: () => void;
}

export const useChatFab = create<ChatFabState>((set) => ({
  open: false,
  openPanel: () => set({ open: true }),
  closePanel: () => set({ open: false }),
  toggle: () => set((s) => ({ open: !s.open })),
}));
