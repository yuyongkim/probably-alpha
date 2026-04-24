// Global test setup — extends `expect` with jest-dom matchers
// (toBeInTheDocument, toHaveClass, etc.) and wires a default cleanup.
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
});
