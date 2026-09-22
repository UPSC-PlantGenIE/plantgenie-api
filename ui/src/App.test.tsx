import { describe, it, expect, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import { Router } from "wouter";
import { memoryLocation } from "wouter/memory-location";
import { renderWithStore } from "./test-utils";
import App from "./App";

describe("App", () => {
  beforeEach(() => localStorage.clear());

  it("prevents non-authenticated users access to authenticated routes", () => {
    const { hook, history } = memoryLocation({ path: "/lists", record: true });

    renderWithStore(
      <Router hook={hook}>
        <App />
      </Router>
    );
    expect(history.at(-1)).toBe("/");
  });

  it("allows authenticated users access to authenticated routes", async () => {
    const { hook } = memoryLocation({ path: "/lists", record: true });

    renderWithStore(
      <Router hook={hook}>
        <App />
      </Router>,
      { preloadedState: { account: { accountId: "1234567890123456" } } }
    );

    expect(
      await screen.findByRole("heading", { name: /my lists/i })
    ).toBeInTheDocument();
  });

  it("renders the landing page at '/'", () => {
    const { hook } = memoryLocation({ path: "/" });
    renderWithStore(
      <Router hook={hook}>
        <App />
      </Router>
    );
    expect(
      screen.getByRole("textbox", { name: /account id/i })
    ).toBeInTheDocument();
  });

  it("renders the My Lists page at '/lists'", () => {
    const { hook } = memoryLocation({ path: "/lists" });
    renderWithStore(
      <Router hook={hook}>
        <App />
      </Router>,
      { preloadedState: { account: { accountId: "1234567890123456" } } }
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
      </Router>,
      { preloadedState: { account: { accountId: "1234567890123456" } } }
    );
    expect(
      screen.getByRole("heading", { name: /select a taxon/i })
    ).toBeInTheDocument();
  });

  it("renders the List page at '/lists/:listId'", async () => {
    const { hook } = memoryLocation({ path: "/lists/abc-123" });
    renderWithStore(
      <Router hook={hook}>
        <App />
      </Router>,
      { preloadedState: { account: { accountId: "1234567890123456" } } }
    );
    expect(
      await screen.findByRole("heading", {
        name: /this list has no genes yet/i,
      })
    ).toBeInTheDocument();
  });
});
