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

  it("links to the BLAST page", () => {
    renderWithStore(<Navbar />);
    expect(screen.getByRole("link", { name: /blast/i })).toHaveAttribute(
      "href",
      "/blast"
    );
  });

  it("links the wordmark home", () => {
    renderWithStore(<Navbar />);
    expect(screen.getByRole("link", { name: /PlantGenIE/ })).toHaveAttribute(
      "href",
      "/"
    );
  });

  it("links to the lists page when signed in", () => {
    renderWithStore(<Navbar />, {
      preloadedState: { account: { accountId: "1234567890123456" } },
    });
    expect(screen.getByRole("link", { name: /^lists$/i })).toHaveAttribute(
      "href",
      "/lists"
    );
  });

  it("offers no lists link when signed out", () => {
    renderWithStore(<Navbar />);
    expect(
      screen.queryByRole("link", { name: /^lists$/i })
    ).not.toBeInTheDocument();
  });
});
