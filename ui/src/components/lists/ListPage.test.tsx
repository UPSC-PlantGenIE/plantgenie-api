import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { Route, Router } from "wouter";
import { memoryLocation } from "wouter/memory-location";
import { server } from "../../mocks/server";
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

  it("renders a gene row for each member when the list has genes", async () => {
    server.use(
      http.get(
        "http://localhost:8000/api/v2/lists/:listId",
        ({ params }) => {
          return HttpResponse.json({
            listId: params.listId,
            name: "Populated list",
            description: null,
            annotationId: "arath-Araport11",
            taxonName: "Arabidopsis thaliana",
            createdAt: "2026-04-14 12:00:00",
            geneCount: 2,
            memberGeneIds: ["AT1G01010", "AT1G01020"],
          });
        }
      )
    );
    renderListPage();
    expect(await screen.findByText("AT1G01010")).toBeInTheDocument();
    expect(screen.getByText("AT1G01020")).toBeInTheDocument();
  });

  it("shows the gene description for each member", async () => {
    server.use(
      http.get(
        "http://localhost:8000/api/v2/lists/:listId",
        ({ params }) => {
          return HttpResponse.json({
            listId: params.listId,
            name: "Populated list",
            description: null,
            annotationId: "arath-Araport11",
            taxonName: "Arabidopsis thaliana",
            createdAt: "2026-04-14 12:00:00",
            geneCount: 1,
            memberGeneIds: ["AT1G01010"],
          });
        }
      )
    );
    renderListPage();
    expect(await screen.findByText(/first gene/i)).toBeInTheDocument();
  });
});
