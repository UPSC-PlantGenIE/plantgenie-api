import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { Router } from "wouter";
import { memoryLocation } from "wouter/memory-location";
import { renderWithStore } from "./test-utils";
import App from "./App";

describe("App", () => {
  it("renders the My Lists page at '/'", () => {
    const { hook } = memoryLocation({ path: "/" });
    renderWithStore(
      <Router hook={hook}>
        <App />
      </Router>
    );
    expect(
      screen.getByRole("heading", { name: /my lists/i })
    ).toBeInTheDocument();
  });

  it("renders the wizard at '/lists/new'", () => {
    const { hook } = memoryLocation({ path: "/lists/new" });
    renderWithStore(
      <Router hook={hook}>
        <App />
      </Router>
    );
    expect(
      screen.getByRole("heading", { name: /name your list/i })
    ).toBeInTheDocument();
  });

  it("renders the List page at '/lists/:listId'", async () => {
    const { hook } = memoryLocation({ path: "/lists/abc-123" });
    renderWithStore(
      <Router hook={hook}>
        <App />
      </Router>
    );
    expect(
      await screen.findByRole("heading", {
        name: /this list has no genes yet/i,
      })
    ).toBeInTheDocument();
  });
});
