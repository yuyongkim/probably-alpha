"use client";

import Link from "next/link";

import { Term } from "@/components/shared/Term";

interface TabEntry {
  href: string;
  /** Tab label as it appears in the top nav. */
  label: string;
  /** One-sentence pitch for someone seeing this for the first time. */
  pitch: string;
  /** Plain-Korean explanation aimed at investing beginners. */
  beginner: React.ReactNode;
  /** 3-4 concrete things they can do here. */
  doables: React.ReactNode[];
  /** "처음이라면" entry-point link + label. */
  startHref: string;
  startLabel: string;
  /** Notable practitioners associated with this tab's methodology. */
  practitioners: string[];
}

const TABS: TabEntry[] = [
  {
    href: "/chartist/today",
    label: "Chartist",
    pitch: "차트로 강한 종목·섹터를 찾는다",
    beginner: (
      <>
        시장 전체에서 <strong>오늘 가장 강한 종목과 섹터가 무엇인지</strong>{" "}
        매일 자동 스캔해 보여줍니다. Minervini의{" "}
        <Term k="SEPA">SEPA</Term>, O'Neil의 <Term k="CANSLIM">CANSLIM</Term>{" "}
        등 검증된 룰을 그대로 쓰며, 종목 수를 늘리려고 조건을 절대 완화하지
        않습니다.
      </>
    ),
    doables: [
      <>
        <Term k="TT">TT</Term> 8/8 통과한 주도주 매일 자동 발굴
      </>,
      <>
        섹터별 강도 점수와 로테이션 흐름 시각화
      </>,
      <>
        Minervini · O'Neil · Darvas · Weinstein 등 6 위저드별 화면
      </>,
      <>
        <Term k="VCP">VCP</Term> 수축 · 52주 신고가 돌파 패턴 탐지
      </>,
    ],
    startHref: "/chartist/today",
    startLabel: "오늘의 주도주",
    practitioners: [
      "Mark Minervini",
      "William O'Neil",
      "Nicolas Darvas",
      "Stan Weinstein",
      "Jesse Livermore",
      "Dan Zanger",
    ],
  },
  {
    href: "/quant/factors",
    label: "Quant",
    pitch: "통계와 백테스트로 본다",
    beginner: (
      <>
        "왜 이 주식이 오를까"를 학술 검증된 팩터 모델로 설명합니다.{" "}
        <Term k="Fama-French">Fama-French</Term> 3-팩터/5-팩터,{" "}
        <Term k="Magic Formula">Magic Formula</Term> 같은 전략을 과거 데이터로
        직접 백테스트하고, 매크로 환경이 종목 수익률에 미치는 영향까지 봅니다.
      </>
    ),
    doables: [
      <>
        팩터별 IC (정보계수) 시계열 추적
      </>,
      <>
        SEPA · Magic Formula · QMJ 등 전략 실데이터 백테스트
      </>,
      <>
        매크로 컴퍼스 — 금리·물가·환율의 4-축 레짐 분석
      </>,
      <>
        Walk-forward · Monte Carlo · Black-Litterman 포트폴리오
      </>,
    ],
    startHref: "/quant/factors",
    startLabel: "팩터 화면",
    practitioners: [
      "Eugene Fama",
      "Joel Greenblatt",
      "Cliff Asness",
      "Joseph Piotroski",
      "Edward Altman",
      "Edward Thorp",
    ],
  },
  {
    href: "/value/dcf",
    label: "Value",
    pitch: "회사가 진짜 얼마짜리인지 본다",
    beginner: (
      <>
        "이 주식이 지금 가격보다 더 가치 있는가"를{" "}
        <strong>실제 재무 데이터로</strong> 계산합니다.{" "}
        <Term k="DCF">DCF</Term> 모델, <Term k="ROIC">ROIC</Term>,{" "}
        <Term k="Piotroski F-Score">Piotroski F-Score</Term>,{" "}
        <Term k="Moat">경제적 해자</Term> 분석. <Term k="DART">DART</Term> 공시
        원본을 <Term k="PIT">시점 기준</Term>으로 가져와 백테스트 안전성도
        보장합니다.
      </>
    ),
    doables: [
      <>
        DCF 모델 · WACC 계산 · 안전마진(MoS) 자동 계산
      </>,
      <>
        Piotroski 9-점 · Altman 5-요소 부도 위험 점수
      </>,
      <>
        Magic Formula · QMJ · 경제적 해자 v2 등급 분석
      </>,
      <>
        DART 공시 자동 요약 · 사업부문 매출 분해 · 컨센서스
      </>,
    ],
    startHref: "/value/dcf",
    startLabel: "DCF 모델",
    practitioners: [
      "Warren Buffett",
      "Charlie Munger",
      "Benjamin Graham",
      "Peter Lynch",
      "Howard Marks",
      "Phil Fisher",
    ],
  },
  {
    href: "/execute/overview",
    label: "Execute",
    pitch: "실시간 시세와 주문",
    beginner: (
      <>
        한국투자증권 <Term k="KIS">KIS</Term> OpenAPI를 직접 연결해{" "}
        <strong>실시간 호가, 체결, 계좌 정보</strong>를 봅니다. 호가 스트리밍과
        틱 데이터를 SSE로 실시간 수신. 일부 기능 (실주문, 알고 트레이딩, 자동
        배포)은 KIS TR 추가 구현 필요.
      </>
    ),
    doables: [
      <>
        실시간 호가창 (H0STASP0) · 체결 스트림 (H0STCNT0)
      </>,
      <>
        외인·기관 누적 수급 · 프로그램 매매 등락 폭 모니터링
      </>,
      <>
        백테스트 결과 리스트 + 상세 (CAGR · MDD · Sharpe)
      </>,
      <>
        주문/포지션/리스크 페이지 (일부 ROADMAP)
      </>,
    ],
    startHref: "/execute/overview",
    startLabel: "Overview",
    practitioners: [
      "Stanley Druckenmiller",
      "Paul Tudor Jones",
      "George Soros",
      "Jim Simons",
      "Bruce Kovner",
      "Michael Marcus",
    ],
  },
  {
    href: "/research/airesearch",
    label: "Research",
    pitch: "AI에게 자연어로 질문한다",
    beginner: (
      <>
        도서 41K + 한국은행 367K + 증권사 197K = 605K 청크를 학습한 AI에게{" "}
        <strong>한국어로 자유롭게 질문</strong>할 수 있습니다. 답변마다 어떤
        보고서 어느 페이지에서 가져온 정보인지 출처가 붙습니다. 환각 없는 RAG
        구조라 ChatGPT처럼 만들어내지 않습니다.
      </>
    ),
    doables: [
      <>
        "2022년 금리 인상기에 한은이 무엇을 우려했는지" 같은 질문
      </>,
      <>
        학술 논문 (Fama-French · Greenblatt · Piotroski) 재현 카탈로그
      </>,
      <>
        한국 증권사 리포트 22K건 인덱싱 · 출처별 검색
      </>,
      <>
        버핏 서한 · 시장 심리 · 경제 사이클 별도 RAG
      </>,
    ],
    startHref: "/research/airesearch",
    startLabel: "AI Research",
    practitioners: [
      "Daniel Kahneman",
      "Nassim Taleb",
      "Benoit Mandelbrot",
      "Robert Shiller",
      "Howard Marks",
      "Aswath Damodaran",
    ],
  },
  {
    href: "/admin/status",
    label: "Admin",
    pitch: "시스템 운영",
    beginner: (
      <>
        데이터 수집 자동화 · 어댑터 헬스체크 · 사용량 추적 · 감사 로그.
        멀티테넌트 운영을 위한 백오피스. 평소엔 안 들여다봐도 되지만,
        <strong> 데이터가 멈췄을 때 첫 진단</strong>이 여기서 시작됩니다.
      </>
    ),
    doables: [
      <>
        시스템 상태 · API 키 존재 여부 · DB 통계
      </>,
      <>
        매일/매주 자동화 잡 (nightly · weekly) 실행 결과
      </>,
      <>
        7개 데이터 어댑터 (KIS·DART·FRED·ECOS·KOSIS·EIA·EXIM) 헬스
      </>,
      <>
        테넌트 CRUD · API 키 로테이션 · 감사 로그
      </>,
    ],
    startHref: "/admin/status",
    startLabel: "Status",
    practitioners: ["당신", "DevOps", "데이터 엔지니어"],
  },
];

export function TabDirectory() {
  return (
    <section className="mb-14">
      <div className="flex items-baseline justify-between mb-6 flex-wrap gap-2">
        <h2 className="display text-2xl md:text-3xl tracking-tight">
          탭 바로가기
        </h2>
        <span className="mono text-[10.5px] text-[color:var(--fg-muted)]">
          6 TABS · 124 SUBSECTIONS
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {TABS.map((t) => (
          <article
            key={t.href}
            className="rounded-md border flex flex-col"
            style={{
              borderColor: "var(--border)",
              background: "var(--surface)",
            }}
          >
            <Link
              href={t.href as never}
              className="block p-5 md:p-6 group transition-colors hover:bg-[color:var(--bg)]"
            >
              {/* Header */}
              <div className="flex items-baseline justify-between mb-2">
                <span
                  className="text-xl md:text-[22px] font-bold tracking-tight"
                  style={{ color: "var(--fg)", letterSpacing: "-0.02em" }}
                >
                  {t.label}
                </span>
                <span
                  className="text-[11px] mono opacity-0 group-hover:opacity-100 transition-opacity"
                  style={{ color: "var(--accent)" }}
                >
                  →
                </span>
              </div>
              <p
                className="text-[13px] mb-3 italic"
                style={{ color: "var(--accent)" }}
              >
                {t.pitch}
              </p>

              {/* Beginner explanation */}
              <p
                className="text-[12.5px] leading-relaxed mb-4"
                style={{ color: "var(--fg)" }}
              >
                {t.beginner}
              </p>

              {/* Doables list */}
              <div
                className="border-t pt-3 mb-3"
                style={{ borderColor: "var(--border-soft)" }}
              >
                <div
                  className="text-[9.5px] uppercase tracking-widest mono mb-2"
                  style={{ color: "var(--muted)" }}
                >
                  여기서 할 수 있는 일
                </div>
                <ul className="space-y-1.5">
                  {t.doables.map((d, i) => (
                    <li
                      key={i}
                      className="text-[11.5px] leading-relaxed flex items-baseline gap-2"
                      style={{ color: "var(--fg-muted)" }}
                    >
                      <span
                        className="inline-block w-1 h-1 rounded-full mt-1.5 shrink-0"
                        style={{ background: "var(--accent)" }}
                      />
                      <span>{d}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Practitioners — who's known for this style */}
              <div
                className="border-t pt-3"
                style={{ borderColor: "var(--border-soft)" }}
              >
                <div
                  className="text-[9.5px] uppercase tracking-widest mono mb-2"
                  style={{ color: "var(--muted)" }}
                >
                  유명 실천자
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {t.practitioners.map((p) => (
                    <span
                      key={p}
                      className="inline-block px-2 py-0.5 rounded-full text-[10.5px] border"
                      style={{
                        borderColor: "var(--border-soft)",
                        color: "var(--fg-muted)",
                        background: "var(--bg)",
                      }}
                    >
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            </Link>

            {/* "처음이라면" entry CTA */}
            <Link
              href={t.startHref as never}
              className="border-t px-5 md:px-6 py-3 flex items-baseline justify-between text-[12px] transition-colors hover:bg-[color:var(--accent-soft)]"
              style={{
                borderColor: "var(--border-soft)",
                color: "var(--fg-muted)",
              }}
            >
              <span>
                <span
                  className="mono uppercase tracking-wider mr-2 text-[10px]"
                  style={{ color: "var(--muted)" }}
                >
                  처음이라면
                </span>
                <span style={{ color: "var(--accent)" }}>
                  {t.startLabel}
                </span>
                {" "}에서 시작
              </span>
              <span style={{ color: "var(--accent)" }}>→</span>
            </Link>
          </article>
        ))}
      </div>
    </section>
  );
}
