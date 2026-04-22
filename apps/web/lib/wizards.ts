// Wizard presets — one object per trader persona used by
// /chartist/wizards/[name]. Keeps page.tsx small.

export interface WizardConfig {
  key: string;
  name: string;
  quote: string;
  rules: string[];
}

export const WIZARDS: WizardConfig[] = [
  {
    key: "minervini",
    name: "Mark Minervini",
    quote:
      "The market does not reward everyone. It rewards those who wait for the right setup.",
    rules: [
      "Trend Template 8조건 중 6개 이상 통과",
      "RS 백분위 ≥ 70",
      "VCP 수축 최소 2단계",
    ],
  },
  {
    key: "oneil",
    name: "William O'Neil (CANSLIM)",
    quote:
      "What seems too high and risky to the majority generally goes higher.",
    rules: [
      "RS 백분위 ≥ 80",
      "EPS YoY 성장 확인 (financials_pit)",
      "주가 52주 고점의 90% 이상",
      "Trend Template 5/8+",
    ],
  },
  {
    key: "darvas",
    name: "Nicolas Darvas",
    quote: "I only look at stocks that are making new highs.",
    rules: [
      "최근 20일 박스권 폭 2–10%",
      "당일 종가가 박스 상단 돌파",
      "거래량 ≥ 50일 평균의 1.5배",
    ],
  },
  {
    key: "livermore",
    name: "Jesse Livermore",
    quote: "The big money is made in the big swings — follow the line of least resistance.",
    rules: [
      "60일 신고가 돌파 (피벗)",
      "20일 블록 기준 연속 HH 상승",
      "Close > SMA50 > SMA200",
    ],
  },
  {
    key: "zanger",
    name: "Dan Zanger",
    quote: "Volume is the fuel — without it, a breakout is a head-fake.",
    rules: [
      "Gap-up ≥ +3%",
      "Volume ≥ 50일 평균의 1.5배",
      "종가가 당일 고가의 95% 이상",
      "Close > SMA20",
    ],
  },
  {
    key: "weinstein",
    name: "Stan Weinstein",
    quote: "The only stocks worth owning are in Stage 2 advancing phases.",
    rules: [
      "Stage 2: SMA30(weekly ≈ 150d) 돌파 + 상승",
      "SMA30 추세 22일 동안 상승",
      "돌파일 거래량 ≥ 50일 평균 × 1.3",
    ],
  },
];

export function getWizardConfig(key: string): WizardConfig | undefined {
  return WIZARDS.find((w) => w.key === key);
}
