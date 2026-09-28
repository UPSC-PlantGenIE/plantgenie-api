import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import Heatmap from "./Heatmap";

const genes = ["PA_chr01_G000102", "PA_chr01_G000106"];
const samples = [
  { id: "control-1", group: 1, order: 1 },
  { id: "cold-1", group: 2, order: 2 },
];
const values = [
  [0, 10],
  [5, 2],
];

describe("Heatmap", () => {
  it("renders a cell for each gene and sample", () => {
    const { container } = render(
      <Heatmap genes={genes} samples={samples} values={values} />
    );
    expect(container.querySelectorAll("rect[data-cell]")).toHaveLength(4);
    expect(screen.getByText("PA_chr01_G000102")).toBeInTheDocument();
    expect(screen.getByText("PA_chr01_G000106")).toBeInTheDocument();
  });

  it("drops both label sets when labels are off", () => {
    const { container } = render(
      <Heatmap
        genes={genes}
        samples={samples}
        values={values}
        showLabels={false}
      />
    );
    expect(container.querySelectorAll("rect[data-cell]")).toHaveLength(4);
    expect(container.querySelectorAll("text")).toHaveLength(0);
  });

  it("scales down to fit its container", () => {
    const { container } = render(
      <Heatmap genes={genes} samples={samples} values={values} />
    );
    expect(container.querySelector("svg")).toHaveClass("max-w-full");
  });

  it("gives the highest and lowest values different fills", () => {
    const { container } = render(
      <Heatmap genes={genes} samples={samples} values={values} />
    );
    const cells = container.querySelectorAll("rect[data-cell]");
    const lowest = cells[0].getAttribute("fill");
    const highest = cells[1].getAttribute("fill");
    expect(lowest).not.toEqual(highest);
  });
});
