// Tests for components/home/PillCard.tsx — KPI pill renderer.
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { PillCard } from "@/components/home/PillCard";
import type { KpiPill } from "@/types/today";

describe("PillCard", () => {
  const base: KpiPill = { label: "KOSPI", value: "2,650.12" };

  it("renders label and value", () => {
    render(<PillCard pill={base} />);
    expect(screen.getByText("KOSPI")).toBeInTheDocument();
    expect(screen.getByText("2,650.12")).toBeInTheDocument();
  });

  it("omits delta node when delta is undefined", () => {
    const { container } = render(<PillCard pill={base} />);
    // Outer wrapper has label + value as direct children; no delta.
    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper.children.length).toBe(2);
  });

  it("includes delta node when delta is provided", () => {
    const pill: KpiPill = { ...base, delta: "+1.2%", tone: "pos" };
    const { container } = render(<PillCard pill={pill} />);
    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper.children.length).toBe(3);
  });

  it("tone=pos applies --pos color to delta", () => {
    const pill: KpiPill = { ...base, delta: "+1.2%", tone: "pos" };
    render(<PillCard pill={pill} />);
    const delta = screen.getByText("+1.2%");
    expect(delta).toHaveStyle({ color: "var(--pos)" });
  });

  it("tone=neg applies --neg color to delta", () => {
    const pill: KpiPill = { ...base, delta: "-0.5%", tone: "neg" };
    render(<PillCard pill={pill} />);
    const delta = screen.getByText("-0.5%");
    expect(delta).toHaveStyle({ color: "var(--neg)" });
  });

  it("tone=neutral falls through to muted color", () => {
    const pill: KpiPill = { ...base, delta: "0.0%", tone: "neutral" };
    render(<PillCard pill={pill} />);
    const delta = screen.getByText("0.0%");
    expect(delta).toHaveStyle({ color: "var(--fg-muted)" });
  });

  it("compact=true uses smaller font classes", () => {
    render(<PillCard pill={base} compact />);
    // The `mono` span carries the value — when compact, it's `text-[13px]`.
    const value = screen.getByText("2,650.12");
    expect(value.className).toContain("text-[13px]");
    expect(value.className).not.toContain("text-lg");
  });

  it("compact=false (default) uses text-lg for value", () => {
    render(<PillCard pill={base} />);
    const value = screen.getByText("2,650.12");
    expect(value.className).toContain("text-lg");
  });
});
