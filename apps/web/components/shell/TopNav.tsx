// TopNav — brand + 6-tab pill nav + search + avatar.
// Client component so it can use usePathname() for active-tab detection.
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brand } from "@/components/shell/Brand";

const TABS = [
  { id: "chartist", href: "/chartist/today", label: "Chartist" },
  { id: "quant", href: "/quant/factors", label: "Quant" },
  { id: "value", href: "/value/dcf", label: "Value" },
  { id: "execute", href: "/execute/overview", label: "Execute" },
  { id: "research", href: "/research/papers", label: "Research" },
  { id: "admin", href: "/admin/status", label: "Admin" },
];

function currentTabId(pathname: string): string | null {
  const seg = pathname.split("/").filter(Boolean)[0];
  return seg ?? null;
}

export function TopNav() {
  const pathname = usePathname() || "/";
  const active = currentTabId(pathname);

  return (
    <header className="topnav">
      <div className="topnav-inner">
        <Brand />
        <nav className="main-nav">
          {TABS.map((t) => (
            <Link
              key={t.id}
              href={t.href as never}
              className={`tab-link ${active === t.id ? "active" : ""}`}
            >
              {t.label}
            </Link>
          ))}
        </nav>
        <div className="header-right">
          <div
            className="search-box"
            role="button"
            tabIndex={0}
            aria-label="Search tickers, sectors, strategies"
          >
            <span>종목·섹터·전략 검색</span>
            <kbd>⌘K</kbd>
          </div>
          <div className="avatar" aria-label="User menu">
            YK
          </div>
        </div>
      </div>
    </header>
  );
}
