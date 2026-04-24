// Tests for components/home/TopSectorsList.tsx — top sector pill list.
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TopSectorsList } from "@/components/home/TopSectorsList";
import type { TodaySector } from "@/types/today";

function makeRow(i: number, overrides: Partial<TodaySector> = {}): TodaySector {
  return {
    rank: i,
    name: `섹터${i}`,
    score: 0.5 + i * 0.01,
    d1: i % 2 === 0 ? 1.25 : -0.87,
    ...overrides,
  };
}

describe("TopSectorsList", () => {
  it("renders at most 8 rows even when given more", () => {
    const rows = Array.from({ length: 15 }, (_, i) => makeRow(i + 1));
    const { container } = render(<TopSectorsList rows={rows} />);
    expect(container.querySelectorAll("li").length).toBe(8);
  });

  it("renders fewer rows when given fewer", () => {
    const rows = Array.from({ length: 3 }, (_, i) => makeRow(i + 1));
    const { container } = render(<TopSectorsList rows={rows} />);
    expect(container.querySelectorAll("li").length).toBe(3);
  });

  it("formats d1 as signed percentage", () => {
    const rows = [makeRow(1, { d1: 2.5 }), makeRow(2, { d1: -1.75 })];
    render(<TopSectorsList rows={rows} />);
    expect(screen.getByText("+2.50%")).toBeInTheDocument();
    expect(screen.getByText("-1.75%")).toBeInTheDocument();
  });

  it("applies pos color to positive d1 and neg to negative", () => {
    const rows = [makeRow(1, { d1: 2.5 }), makeRow(2, { d1: -1.75 })];
    render(<TopSectorsList rows={rows} />);
    expect(screen.getByText("+2.50%")).toHaveStyle({ color: "var(--pos)" });
    expect(screen.getByText("-1.75%")).toHaveStyle({ color: "var(--neg)" });
  });

  it("renders dash when d1 is null", () => {
    const rows = [makeRow(1, { d1: null as unknown as number })];
    render(<TopSectorsList rows={rows} />);
    // fmtPct(null) → "—"
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("renders score with two decimals when present", () => {
    const rows = [makeRow(1, { score: 0.873 })];
    render(<TopSectorsList rows={rows} />);
    expect(screen.getByText("0.87")).toBeInTheDocument();
  });

  it("omits score span when score is undefined", () => {
    const rows = [makeRow(1, { score: undefined })];
    const { container } = render(<TopSectorsList rows={rows} />);
    // Row should still render, but without score text.
    expect(container.querySelectorAll("li").length).toBe(1);
    expect(screen.queryByText(/^0\.\d{2}$/)).not.toBeInTheDocument();
  });

  it("displays rank prefix and sector name", () => {
    render(<TopSectorsList rows={[makeRow(1, { name: "반도체" })]} />);
    expect(screen.getByText("1.")).toBeInTheDocument();
    expect(screen.getByText("반도체")).toBeInTheDocument();
  });
});
