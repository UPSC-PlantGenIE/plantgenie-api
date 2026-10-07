import { describe, it, expect } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { Route, Router } from "wouter";
import { memoryLocation } from "wouter/memory-location";
import { server } from "../../mocks/server";
import { renderWithStore } from "../../test-utils";
import SemanticSearchPage from "./SemanticSearchPage";

const API = "http://localhost:8000/api/v2";

const renderPage = () => {
  const requested: string[] = [];
  server.use(
    http.get(`${API}/semantic-search/species`, () =>
      HttpResponse.json([
        { abbreviation: "arath", scientificName: "Arabidopsis thaliana" },
      ])
    ),
    http.get(`${API}/semantic-search`, ({ request }) => {
      const url = new URL(request.url);
      requested.push(url.searchParams.get("number_of_results") ?? "");
      return HttpResponse.json([
        { geneId: "AT1G01010", description: "First gene", similarity: 0.9 },
      ]);
    })
  );
  const { hook } = memoryLocation({ path: "/lists/abc-123/search" });
  renderWithStore(
    <Router hook={hook}>
      <Route path="/lists/:listId/search" component={SemanticSearchPage} />
    </Router>
  );
  return requested;
};

const search = async (text: string) => {
  const user = userEvent.setup();
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Search" })).toBeDisabled()
  );
  await user.type(screen.getByLabelText("Search query"), text);
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Search" })).toBeEnabled()
  );
  await user.click(screen.getByRole("button", { name: "Search" }));
  return user;
};

describe("SemanticSearchPage", () => {
  it("suggests the topic of an '<x> in <species>' list title; Tab fills it", async () => {
    server.use(
      http.get(`${API}/lists/:listId`, ({ params }) =>
        HttpResponse.json({
          listId: params.listId,
          name: "dehydration in Arabidopsis thaliana",
          description: null,
          annotationId: "arath-Araport11",
          taxonName: "Arabidopsis thaliana",
          createdAt: "2026-04-14 12:00:00",
          geneCount: 1,
          memberGeneIds: ["AT1G01010"],
        })
      )
    );
    renderPage();
    const input = screen.getByLabelText("Search query");
    await waitFor(() =>
      expect(input).toHaveAttribute("placeholder", "e.g. dehydration")
    );
    const user = userEvent.setup();
    await user.click(input);
    await user.tab();
    expect(input).toHaveValue("dehydration");
    expect(input).toHaveFocus();
  });

  it("requests 10 results by default", async () => {
    const requested = renderPage();
    await search("kinase");
    await screen.findByText("AT1G01010");
    expect(requested).toEqual(["10"]);
    expect(screen.getByLabelText("Results to show")).toHaveValue(10);
  });

  it("re-runs the search with a custom number of results", async () => {
    const requested = renderPage();
    const user = await search("kinase");
    await screen.findByText("AT1G01010");

    await user.click(screen.getByRole("button", { name: "100" }));
    await waitFor(() => expect(requested).toContain("100"));

    const input = screen.getByLabelText("Results to show");
    await user.clear(input);
    await user.type(input, "5000{Enter}");
    await waitFor(() => expect(requested).toContain("5000"));
  });
});
