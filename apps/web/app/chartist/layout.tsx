// Chartist layout — shared sub-navigation for the 6 sub-sections.
import Link from "next/link";

const SUBTABS = [
  { href: "/chartist/today", label: "Today" },
  { href: "/chartist/leaders", label: "Leaders" },
  { href: "/chartist/sectors", label: "Sectors" },
  { href: "/chartist/breakouts", label: "Breakouts" },
  { href: "/chartist/breadth", label: "Breadth" },
  { href: "/chartist/wizards", label: "Wizards" },
];

export default function ChartistLayout({ children }: { children: React.ReactNode }) {
  return (
    <section>
      <div className="text-xs uppercase tracking-widest text-[color:var(--muted)] mb-2">
        Chartist
      </div>
      <nav
        className="flex flex-wrap gap-1 mb-4 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        {SUBTABS.map((t) => (
          <Link
            key={t.href}
            href={t.href as never}
            className="px-3 py-2 text-[13px] text-[color:var(--fg-muted)] hover:text-[color:var(--fg)] border-b-2 border-transparent hover:border-[color:var(--accent)] transition-colors"
          >
            {t.label}
          </Link>
        ))}
      </nav>
      {children}
    </section>
  );
}
