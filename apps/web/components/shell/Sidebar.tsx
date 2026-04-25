// Sidebar — renders the group/link tree for the current top-level tab.
// Client because usePathname() decides which group set + which link is active.
// On the root path "/" we render a Home-mode sidebar that surfaces every
// tab's headline entry point so the visitor doesn't see an empty aside.
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  SIDEBAR_MAP,
  getTabFromPathname,
  type SidebarGroup,
  type SidebarLink,
  type TabKey,
} from "@/lib/sidebarMap";

function LinkRow({ link, active }: { link: SidebarLink; active: boolean }) {
  const classes = [
    "sidebar-link",
    link.sub ? "sub" : "",
    active ? "active" : "",
  ]
    .filter(Boolean)
    .join(" ");
  const body = (
    <>
      <span>{link.label}</span>
      {link.count !== undefined && <span className="count">{link.count}</span>}
    </>
  );
  if (link.href) {
    return (
      <Link href={link.href as never} className={classes}>
        {body}
      </Link>
    );
  }
  return (
    <button type="button" className={classes} disabled>
      {body}
    </button>
  );
}

function Group({ group, pathname }: { group: SidebarGroup; pathname: string }) {
  return (
    <>
      <div className="sidebar-label">{group.label}</div>
      {group.links.map((l) => (
        <LinkRow key={l.label} link={l} active={l.href === pathname} />
      ))}
    </>
  );
}

// Home-mode shortcuts — one entry point per tab, plus the AI chat. Picked
// to be the most useful "first click" for a brand-new visitor.
interface HomeShortcut {
  label: string;
  href: string;
  count?: string;
}
const HOME_GROUPS: { label: string; links: HomeShortcut[] }[] = [
  {
    label: "Start here",
    links: [
      { label: "AI에게 질문하기", href: "/research/airesearch" },
      { label: "오늘의 주도주", href: "/chartist/today" },
      { label: "시스템 상태", href: "/admin/status" },
    ],
  },
  {
    label: "Chartist · 차트",
    links: [
      { label: "오늘의 주도주", href: "/chartist/today" },
      { label: "Leader 전체", href: "/chartist/leaders" },
      { label: "섹터 강도", href: "/chartist/sectors" },
      { label: "Market Wizards", href: "/chartist/wizards" },
    ],
  },
  {
    label: "Quant · 팩터",
    links: [
      { label: "팩터", href: "/quant/factors" },
      { label: "매크로 컴퍼스", href: "/quant/macro" },
      { label: "백테스트", href: "/quant/qbacktest" },
    ],
  },
  {
    label: "Value · 재무",
    links: [
      { label: "DCF 모델", href: "/value/dcf" },
      { label: "ROIC", href: "/value/roic" },
      { label: "Piotroski", href: "/value/piotroski" },
      { label: "Magic Formula", href: "/value/magic" },
    ],
  },
  {
    label: "Research · AI",
    links: [
      { label: "AI Research", href: "/research/airesearch" },
      { label: "지식 베이스", href: "/research/knowledge" },
      { label: "한국 리포트", href: "/research/krreports" },
      { label: "버핏 RAG", href: "/research/buffettletters" },
    ],
  },
  {
    label: "Execute · 실행",
    links: [
      { label: "Overview", href: "/execute/overview" },
      { label: "호가창", href: "/execute/orderbook" },
      { label: "WebSocket 라이브", href: "/execute/websocket" },
    ],
  },
  {
    label: "Admin · 운영",
    links: [
      { label: "Status", href: "/admin/status" },
      { label: "데이터 헬스", href: "/admin/data" },
      { label: "API 키", href: "/admin/keys" },
    ],
  },
];

function HomeSidebar({ pathname }: { pathname: string }) {
  return (
    <aside className="sidebar" aria-label="Home shortcuts">
      <div className="sidebar-group active">
        {HOME_GROUPS.map((g, i) => (
          <div key={g.label}>
            <div className="sidebar-label">{g.label}</div>
            {g.links.map((l) => (
              <LinkRow
                key={l.href}
                link={l as SidebarLink}
                active={l.href === pathname}
              />
            ))}
            {i < HOME_GROUPS.length - 1 && <div className="sidebar-divider" />}
          </div>
        ))}
      </div>
    </aside>
  );
}

export function Sidebar() {
  const pathname = usePathname() || "/";
  const tab = getTabFromPathname(pathname);

  // Root or unrecognised path → show curated home shortcuts instead of blank.
  if (!tab) {
    return <HomeSidebar pathname={pathname} />;
  }

  const groups = SIDEBAR_MAP[tab as TabKey];
  return (
    <aside className="sidebar" aria-label="Sidebar navigation">
      <div className="sidebar-group active">
        {groups.map((g, i) => (
          <div key={g.label}>
            <Group group={g} pathname={pathname} />
            {i < groups.length - 1 && <div className="sidebar-divider" />}
          </div>
        ))}
      </div>
    </aside>
  );
}
