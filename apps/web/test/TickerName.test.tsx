// Tests for components/shared/TickerName.tsx — the click-to-open-modal label.
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// Mock the zustand store before importing the component.
const openModalMock = vi.fn();
vi.mock("@/lib/stockModal", () => ({
  // The real hook is called like `useStockModal((s) => s.openModal)`.
  // Accept the selector and return whatever it picks from our fake state.
  useStockModal: (selector: (state: { openModal: typeof openModalMock }) => unknown) =>
    selector({ openModal: openModalMock }),
}));

import { TickerName } from "@/components/shared/TickerName";

describe("TickerName", () => {
  beforeEach(() => {
    openModalMock.mockReset();
  });

  it("renders a native <button> element (not span[role=button])", () => {
    render(<TickerName symbol="005930" name="삼성전자" />);
    const btn = screen.getByRole("button", { name: "삼성전자" });
    expect(btn.tagName).toBe("BUTTON");
    expect(btn).toHaveAttribute("type", "button");
  });

  it("click calls openModal with (symbol, name, sector)", async () => {
    const user = userEvent.setup();
    render(<TickerName symbol="005930" name="삼성전자" sector="반도체" />);
    await user.click(screen.getByRole("button", { name: "삼성전자" }));
    expect(openModalMock).toHaveBeenCalledTimes(1);
    expect(openModalMock).toHaveBeenCalledWith({
      symbol: "005930",
      name: "삼성전자",
      sector: "반도체",
    });
  });

  it("children prop overrides name display", () => {
    render(
      <TickerName symbol="035420" name="네이버">
        NAVER Corp
      </TickerName>,
    );
    expect(screen.getByRole("button", { name: "NAVER Corp" })).toBeInTheDocument();
    expect(screen.queryByText("네이버")).not.toBeInTheDocument();
  });

  it("applies ticker-name class plus optional className", () => {
    render(
      <TickerName symbol="005930" name="삼성전자" className="extra-class" />,
    );
    const btn = screen.getByRole("button");
    expect(btn).toHaveClass("ticker-name");
    expect(btn).toHaveClass("extra-class");
  });
});
