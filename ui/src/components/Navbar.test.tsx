import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import Navbar from "./Navbar";
import { renderWithStore } from "../test-utils";

describe("Navbar", () => {
  it("renders the PlantGenIE wordmark", () => {
    renderWithStore(<Navbar />);
    expect(screen.getByText(/PlantGenIE/)).toBeInTheDocument();
  });

  it("exposes a banner landmark", () => {
    renderWithStore(<Navbar />);
    expect(screen.getByRole("banner")).toBeInTheDocument();
  });
});
