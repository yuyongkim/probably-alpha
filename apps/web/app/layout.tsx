import type { Metadata } from "next";
import Link from "next/link";
import "@/styles/globals.css";
import { StockDetailModalMount } from "@/components/shared/modals/StockDetailModalMount";

export const metadata: Metadata = {
  title: "ky-platform",
  description: "probably-alpha unified financial platform",
};

const TABS = [
  { href: "/chartist/today", label: "Chartist" },
  { href: "/quant/factors", label: "Quant" },
  { href: "/value/dcf", label: "Value" },
  { href: "/execute/overview", label: "Execute" },
  { href: "/research/papers", label: "Research" },
  { href: "/admin/status", label: "Admin" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <header className="border-b border-border px-6 py-3 flex items-center gap-6">
          <Link href="/" className="display text-lg">ky-platform</Link>
          <nav className="flex gap-4 text-sm text-[color:var(--fg-muted)]">
            {TABS.map((t) => (
              <Link key={t.href} href={t.href as never} className="hover:text-[color:var(--fg)]">{t.label}</Link>
            ))}
          </nav>
        </header>
        <main className="px-6 py-8">{children}</main>
        <StockDetailModalMount />
      </body>
    </html>
  );
}
