// NewsAIPane — recent headlines + inline Ask-AI scratchpad (mock).
"use client";

import { useState } from "react";

interface Props {
  symbol: string;
}

interface Headline {
  when: string;
  outlet: string;
  title: string;
  sentiment: "pos" | "neu" | "neg";
}

const SAMPLE: Headline[] = [
  { when: "04-22 09:12", outlet: "연합뉴스",  title: "HBM 수요 초강세, 하반기 쇼티지 지속 전망",        sentiment: "pos" },
  { when: "04-21 18:40", outlet: "Bloomberg", title: "TSMC capex guidance lifts Korea semi equipment",  sentiment: "pos" },
  { when: "04-21 11:24", outlet: "한국경제",  title: "외국인, 반도체 대형주 5일 연속 순매수",            sentiment: "pos" },
  { when: "04-19 17:02", outlet: "매일경제",  title: "중국 수요 둔화 우려, 메모리 재고 일부 재적재",    sentiment: "neg" },
  { when: "04-17 09:00", outlet: "Reuters",   title: "Analyst upgrades 12M target price citing HBM3E",  sentiment: "pos" },
  { when: "04-15 22:11", outlet: "The Elec",  title: "차세대 패키징 공정 국산화율 개선 조짐",            sentiment: "neu" },
];

function sentStyle(s: Headline["sentiment"]): { color: string; bg: string; label: string } {
  if (s === "pos") return { color: "var(--pos)", bg: "var(--pos-soft)", label: "POS" };
  if (s === "neg") return { color: "var(--neg)", bg: "var(--neg-soft)", label: "NEG" };
  return { color: "var(--fg-muted)", bg: "var(--bg)", label: "NEU" };
}

export function NewsAIPane({ symbol }: Props) {
  const [q, setQ] = useState("");
  const [a, setA] = useState<string | null>(null);

  function ask() {
    if (!q.trim()) return;
    // TODO: wire to /api/v1/assistant/ask (Gamma agent).
    setA(
      `(${symbol}) 샘플 답변 — 최근 뉴스 감성은 강한 긍정. HBM3E 수주 모멘텀이 EPS 상향 주도. 다만 중국 수요 둔화가 잠재 리스크.`,
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <section>
        <div className="text-[11px] text-[color:var(--fg-muted)] mb-2">
          최근 헤드라인 · 감성 태깅 (mock)
        </div>
        <ul className="flex flex-col">
          {SAMPLE.map((h, i) => {
            const s = sentStyle(h.sentiment);
            return (
              <li
                key={i}
                className="flex items-center gap-3 py-1.5 px-1 text-[11.5px]"
                style={{ borderBottom: "1px solid var(--border-soft)" }}
              >
                <span className="mono text-[10.5px] text-[color:var(--fg-muted)]">
                  {h.when}
                </span>
                <span className="text-[10.5px] text-[color:var(--muted)]">
                  {h.outlet}
                </span>
                <span className="flex-1">{h.title}</span>
                <span
                  className="px-1.5 py-[1px] rounded text-[10px] font-medium"
                  style={{ color: s.color, background: s.bg }}
                >
                  {s.label}
                </span>
              </li>
            );
          })}
        </ul>
      </section>

      <section
        className="rounded p-3 border"
        style={{ background: "var(--surface-2)", borderColor: "var(--border-soft)" }}
      >
        <div className="text-[11px] text-[color:var(--fg-muted)] mb-2">
          Ask AI about {symbol}
        </div>
        <div className="flex gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="이 종목의 최근 리스크 요인은?"
            className="flex-1 px-2 py-1 rounded text-[12px]"
            style={{
              background: "var(--bg)",
              border: "1px solid var(--border)",
              color: "var(--fg)",
            }}
          />
          <button
            onClick={ask}
            className="px-3 py-1 rounded text-[11px] font-medium"
            style={{ background: "var(--accent)", color: "var(--bg)" }}
          >
            Ask
          </button>
        </div>
        {a && (
          <div className="mt-2 text-[12px] leading-relaxed text-[color:var(--fg)]">
            {a}
          </div>
        )}
      </section>
    </div>
  );
}
