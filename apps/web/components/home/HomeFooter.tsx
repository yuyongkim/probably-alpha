"use client";

import Link from "next/link";

interface Props {
  universeSize?: number;
}

export function HomeFooter({ universeSize }: Props) {
  return (
    <div
      className="text-[11px] text-[color:var(--fg-muted)] border-t pt-3 mt-6"
      style={{ borderColor: "var(--border-soft)" }}
    >
      <div className="flex flex-wrap gap-3">
        <span>
          <span className="mono">GET /api/v1/assistant/health</span> →
          mode=claude
        </span>
        <span>
          RAG: <span className="mono">book + 한은 + 증권사</span> (3 layers)
        </span>
        <Link
          href={"/research/airesearch" as never}
          className="underline hover:text-[color:var(--fg)]"
        >
          AI에게 질문하기
        </Link>
        <Link
          href={"/admin/status" as never}
          className="underline hover:text-[color:var(--fg)]"
        >
          시스템 상태
        </Link>
        {universeSize != null && (
          <span className="ml-auto mono">
            universe {universeSize.toLocaleString()}
          </span>
        )}
      </div>
    </div>
  );
}
