import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../../mocks/server";
import { renderWithStore } from "../../test-utils";
import MyListsPage from "./MyListsPage";

describe("MyListsPage", () => {
  it("renders the heading", () => {
    renderWithStore(<MyListsPage />);
    expect(
      screen.getByRole("heading", { name: /my lists/i })
    ).toBeInTheDocument();
  });

  it("shows a 'create your first list' CTA when there are no lists", async () => {
    server.use(
      http.get("http://localhost:8000/api/v2/lists", () =>
        HttpResponse.json({ lists: [] })
      )
    );
    renderWithStore(<MyListsPage />);
    expect(
      await screen.findByRole("link", { name: /create your first list/i })
    ).toBeInTheDocument();
  });

  it("renders a row for each list", async () => {
    renderWithStore(<MyListsPage />);
    expect(await screen.findByText(/test list/i)).toBeInTheDocument();
  });
});
