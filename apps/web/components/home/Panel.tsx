"use client";

import Link from "next/link";

interface Props {
  title: string;
  href: string;
  children: React.ReactNode;
}

export function Panel({ title, href, children }: Props) {
  return (
    <div
      className="rounded-md border p-3"
      style={{ borderColor: "var(--border)" }}
    >
      <div className="flex items-baseline justify-between mb-2">
        <span className="display text-[13px]">{title}</span>
        <Link
          href={href as never}
          className="text-[10.5px] text-[color:var(--fg-muted)] hover:underline"
        >
          전체보기 →
        </Link>
      </div>
      {children}
    </div>
  );
}

export function EmptyRow({ msg = "데이터 없음 (nightly 파이프라인 대기)." }: { msg?: string }) {
  return (
    <div className="text-[11px] text-[color:var(--fg-muted)] py-3 text-center">
      {msg}
    </div>
  );
}

export function ErrorRow({ msg }: { msg: string }) {
  return (
    <div className="text-[11px] text-[color:var(--neg)] py-3">
      불러오지 못했습니다: {msg}
    </div>
  );
}
