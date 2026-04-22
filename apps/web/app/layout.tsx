// Root shell: fonts + topnav + ticker tape + layout grid (sidebar + content)
// + footer strip + chat FAB/panel. Page content goes in `<main class="content">`.
// Individual pages no longer wrap themselves in headers — the shell owns chrome.
import type { Metadata } from "next";
import "@/styles/globals.css";
import { TopNav } from "@/components/shell/TopNav";
import { TickerTape } from "@/components/shell/TickerTape";
import { Sidebar } from "@/components/shell/Sidebar";
import { FooterStrip } from "@/components/shell/FooterStrip";
import { ChatFab } from "@/components/shell/ChatFab";
import { ChatPanel } from "@/components/shell/ChatPanel";
import { StockDetailModalMount } from "@/components/shared/modals/StockDetailModalMount";

export const metadata: Metadata = {
  title: "Probably Alpha",
  description: "Unified financial platform — Chartist · Quant · Value · Execute · Research",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;0,9..144,600&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <TopNav />
        <TickerTape />
        <div className="layout">
          <Sidebar />
          <main className="content">{children}</main>
        </div>
        <FooterStrip />
        <ChatFab />
        <ChatPanel />
        <StockDetailModalMount />
      </body>
    </html>
  );
}
