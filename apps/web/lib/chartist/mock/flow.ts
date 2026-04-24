// Flow · 수급 대시보드
import type { HeatRow } from "./common";

export const FLOW_SUMMARY = [
  { label: "외국인 당일", value: "+1,247억", delta: "5일 연속 순매수", tone: "pos" as const },
  { label: "기관 당일", value: "+842억", delta: "투신+사모 주도", tone: "pos" as const },
  { label: "프로그램", value: "+584억", delta: "차익 +312 · 비차익 +272", tone: "pos" as const },
  { label: "연기금", value: "+214억", delta: "3일 연속", tone: "pos" as const },
  { label: "개인", value: "−2,087억", delta: "개인 vs 외인+기관", tone: "neg" as const },
  { label: "외인 보유 %", value: "31.8%", delta: "+0.12pp MoM", tone: "pos" as const },
];

export const FLOW_FOREIGN_TOP = [
  { rank: 1, name: "삼성전자", sector: "반도체", d1: 324, d5: 1842, d20: 4281, streak: "12일", pct: 8.7 },
  { rank: 2, name: "SK하이닉스", sector: "반도체", d1: 218, d5: 1124, d20: 2841, streak: "8일", pct: 11.8 },
  { rank: 3, name: "한미반도체", sector: "반도체", d1: 84, d5: 412, d20: 1284, streak: "14일", pct: 22.4 },
  { rank: 4, name: "이수페타시스", sector: "반도체", d1: 62, d5: 284, d20: 842, streak: "7일", pct: 28.3 },
  { rank: 5, name: "두산에너빌리티", sector: "원전", d1: 48, d5: 218, d20: 684, streak: "9일", pct: 19.4 },
  { rank: 6, name: "현대차", sector: "자동차", d1: 42, d5: 184, d20: 412, streak: "4일", pct: 1.4 },
  { rank: 7, name: "KB금융", sector: "금융", d1: 38, d5: 142, d20: 384, streak: "6일", pct: 1.4 },
  { rank: 8, name: "HPSP", sector: "반도체", d1: 32, d5: 124, d20: 342, streak: "8일", pct: 18.7 },
  { rank: 9, name: "NAVER", sector: "AI/SW", d1: 28, d5: 98, d20: 284, streak: "3일", pct: 7.2 },
  { rank: 10, name: "HD현대중공업", sector: "조선", d1: 24, d5: 112, d20: 342, streak: "11일", pct: 8.8 },
];

export const FLOW_INSTITUTION_TOP = [
  { name: "삼성전자", tusin: 82, samo: 48, pension: 124, total: 254 },
  { name: "한미반도체", tusin: 48, samo: 32, pension: 28, total: 108 },
  { name: "SK하이닉스", tusin: 42, samo: 24, pension: 32, total: 98 },
  { name: "두산에너빌리티", tusin: 38, samo: 18, pension: 14, total: 70 },
  { name: "이수페타시스", tusin: 32, samo: 14, pension: 8, total: 54 },
  { name: "현대차", tusin: 28, samo: 12, pension: 12, total: 52 },
  { name: "HPSP", tusin: 24, samo: 12, pension: 8, total: 44 },
  { name: "KB금융", tusin: 18, samo: 8, pension: 14, total: 40 },
  { name: "NAVER", tusin: 22, samo: 8, pension: 6, total: 36 },
  { name: "셀트리온", tusin: 14, samo: 4, pension: 12, total: 30 },
];

export const FLOW_SECTOR_HEATMAP: HeatRow[] = [
  { name: "반도체", cells: [{ v: "+724", h: 6 }, { v: "+3,842", h: 6 }, { v: "+9,282", h: 6 }] },
  { name: "2차전지", cells: [{ v: "+82", h: 4 }, { v: "+184", h: 3 }, { v: "−284", h: 3 }] },
  { name: "AI / SW", cells: [{ v: "+184", h: 5 }, { v: "+682", h: 5 }, { v: "+1,842", h: 5 }] },
  { name: "원전", cells: [{ v: "+148", h: 5 }, { v: "+584", h: 5 }, { v: "+1,482", h: 5 }] },
  { name: "바이오", cells: [{ v: "+18", h: 3 }, { v: "−84", h: 2 }, { v: "−284", h: 2 }] },
  { name: "자동차", cells: [{ v: "+42", h: 4 }, { v: "+184", h: 4 }, { v: "+584", h: 5 }] },
  { name: "조선", cells: [{ v: "+38", h: 4 }, { v: "+184", h: 4 }, { v: "+584", h: 5 }] },
  { name: "금융", cells: [{ v: "+58", h: 4 }, { v: "+182", h: 4 }, { v: "+482", h: 5 }] },
  { name: "방산", cells: [{ v: "−42", h: 2 }, { v: "−284", h: 1 }, { v: "−584", h: 1 }] },
  { name: "화학", cells: [{ v: "−24", h: 2 }, { v: "−84", h: 2 }, { v: "−184", h: 2 }] },
];
