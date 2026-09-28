import { describe, it, expect } from "vitest";
import { cellWidthFor, MAXIMUM_CELL_WIDTH, MINIMUM_CELL_WIDTH } from "./cellWidthFor";

describe("cellWidthFor", () => {
  it("fills the available width when there are few samples", () => {
    expect(cellWidthFor(1000, 20, 150)).toBe(42.5);
  });

  it("never grows past the maximum", () => {
    expect(cellWidthFor(2000, 4, 150)).toBe(MAXIMUM_CELL_WIDTH);
  });

  it("never shrinks past the minimum", () => {
    expect(cellWidthFor(400, 200, 150)).toBe(MINIMUM_CELL_WIDTH);
  });

  it("falls back to the maximum when the container is unmeasured", () => {
    expect(cellWidthFor(0, 20, 150)).toBe(MAXIMUM_CELL_WIDTH);
  });
});
