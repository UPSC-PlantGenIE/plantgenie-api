import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { Route, Router } from "wouter";
import { memoryLocation } from "wouter/memory-location";
import { renderWithStore } from "../../test-utils";
import ListPage from "./ListPage";

const renderListPage = (path = "/lists/abc-123") => {
  const { hook } = memoryLocation({ path });
  return renderWithStore(
    <Router hook={hook}>
      <Route path="/lists/:listId" component={ListPage} />
    </Router>
  );
};

describe("ListPage", () => {
  it("renders the empty-state heading when the list has no genes", async () => {
    renderListPage();
    expect(
      await screen.findByRole("heading", {
        name: /this list has no genes yet/i,
      })
    ).toBeInTheDocument();
  });

  it("shows guidance for adding genes", async () => {
    renderListPage();
    expect(
      await screen.findByText(/add genes by pasting ids/i)
    ).toBeInTheDocument();
  });

  it("has an 'Add by ID' link", async () => {
    renderListPage();
    expect(
      await screen.findByRole("link", { name: /add by id/i })
    ).toBeInTheDocument();
  });

  it("has a 'Search genes' link", async () => {
    renderListPage();
    expect(
      await screen.findByRole("link", { name: /search genes/i })
    ).toBeInTheDocument();
  });

  it("renders the list name fetched from the API", async () => {
    renderListPage();
    expect(
      await screen.findByRole("heading", { name: /my fetched list/i })
    ).toBeInTheDocument();
  });
});
