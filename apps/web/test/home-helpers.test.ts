// Tests for components/home/helpers.ts — pure formatting helpers.
import { describe, it, expect } from "vitest";
import { pctColor, toneColor, cleanSurrogates } from "@/components/home/helpers";

describe("pctColor", () => {
  it("returns muted for null", () => {
    expect(pctColor(null)).toBe("var(--fg-muted)");
  });

  it("returns muted for undefined", () => {
    expect(pctColor(undefined)).toBe("var(--fg-muted)");
  });

  it("returns pos color for positive values", () => {
    expect(pctColor(1.5)).toBe("var(--pos)");
  });

  it("returns pos color for zero (>= 0 branch)", () => {
    expect(pctColor(0)).toBe("var(--pos)");
  });

  it("returns neg color for negative values", () => {
    expect(pctColor(-2.0)).toBe("var(--neg)");
  });
});

describe("toneColor", () => {
  it("pos → var(--pos)", () => {
    expect(toneColor("pos")).toBe("var(--pos)");
  });

  it("neg → var(--neg)", () => {
    expect(toneColor("neg")).toBe("var(--neg)");
  });

  it("neutral → muted", () => {
    expect(toneColor("neutral")).toBe("var(--fg-muted)");
  });

  it("undefined → muted", () => {
    expect(toneColor(undefined)).toBe("var(--fg-muted)");
  });

  it("unknown string → muted", () => {
    expect(toneColor("warning")).toBe("var(--fg-muted)");
  });
});

describe("cleanSurrogates", () => {
  it("returns empty string for null", () => {
    expect(cleanSurrogates(null)).toBe("");
  });

  it("returns empty string for undefined", () => {
    expect(cleanSurrogates(undefined)).toBe("");
  });

  it("preserves normal Korean text", () => {
    expect(cleanSurrogates("삼성전자")).toBe("삼성전자");
  });

  it("strips lone high surrogate", () => {
    const dirty = `SK\uD83D하이닉스`;
    expect(cleanSurrogates(dirty)).toBe("SK하이닉스");
  });

  it("strips lone low surrogate", () => {
    const dirty = `카카오\uDCA9`;
    expect(cleanSurrogates(dirty)).toBe("카카오");
  });

  it("keeps ASCII untouched", () => {
    expect(cleanSurrogates("Hello World")).toBe("Hello World");
  });
});
