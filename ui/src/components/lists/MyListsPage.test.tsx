import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { plantgenieApi, type GeneList } from "../../api/plantgenieApi";
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

  it("shows newly created lists without a remount", async () => {
    let lists: GeneList[] = [];
    server.use(
      http.get("http://localhost:8000/api/v2/lists", () =>
        HttpResponse.json({ lists })
      ),
      http.post("http://localhost:8000/api/v2/lists", async () => {
        lists = [
          {
            listId: "new-1",
            name: "Brand new list",
            description: null,
            annotationId: "arath-Araport11",
            taxonName: "Arabidopsis thaliana",
            createdAt: "2026-04-14T12:00:00",
            geneCount: 0,
          },
        ];
        return HttpResponse.json({
          accountId: "stub",
          listId: "new-1",
        });
      })
    );

    const { store } = renderWithStore(<MyListsPage />);

    await screen.findByRole("link", { name: /create your first list/i });

    await store.dispatch(
      plantgenieApi.endpoints.createList.initiate({
        name: "Brand new list",
        annotationId: "arath-Araport11",
        taxonName: "Arabidopsis thaliana",
      })
    );

    expect(
      await screen.findByText(/brand new list/i)
    ).toBeInTheDocument();
  });
});
