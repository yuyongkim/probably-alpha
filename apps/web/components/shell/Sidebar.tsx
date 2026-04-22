// Sidebar — renders the group/link tree for the current top-level tab.
// Client because usePathname() decides which group set + which link is active.
// If the user is on a tab with no sidebar map, renders an empty aside.
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  SIDEBAR_MAP,
  getTabFromPathname,
  type SidebarGroup,
  type SidebarLink,
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

export function Sidebar() {
  const pathname = usePathname() || "/";
  const tab = getTabFromPathname(pathname);
  if (!tab) {
    return <aside className="sidebar" aria-label="Sidebar navigation" />;
  }
  const groups = SIDEBAR_MAP[tab];
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
