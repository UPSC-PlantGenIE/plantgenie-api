import { describe, it, expect, beforeEach } from "vitest";
import { screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { Route, Router } from "wouter";
import { memoryLocation } from "wouter/memory-location";
import { server } from "../../mocks/server";
import { renderWithStore } from "../../test-utils";
import GenePage from "./GenePage";

const renderGenePage = (
  path = "/genes/pinsy-Araport11/AT1G01010"
) => {
  const { hook } = memoryLocation({ path });
  return renderWithStore(
    <Router hook={hook}>
      <Route
        path="/genes/:annotationId/:geneId"
        component={GenePage}
      />
    </Router>
  );
};

const mockAnnotation = () =>
  server.use(
    http.get(
      "http://localhost:8000/api/v2/annotations/pinsy-Araport11",
      () =>
        HttpResponse.json({
          id: "pinsy-Araport11",
          version: "Araport11",
          geneCount: 27655,
          isDefault: true,
          assemblyId: "pinsy-v2.0",
          taxonAbbreviation: "pinsy",
          taxonScientificName: "Pinus sylvestris",
        })
    )
  );

describe("GenePage", () => {
  beforeEach(() => {
    window.history.replaceState(null, "");
  });

  it("renders the gene id from the URL as the page heading", async () => {
    mockAnnotation();
    renderGenePage();
    expect(
      await screen.findByRole("heading", { name: "AT1G01010" })
    ).toBeInTheDocument();
  });

  it("renders the gene name and description from the lookup", async () => {
    mockAnnotation();
    renderGenePage();
    expect(await screen.findByText("GENE1")).toBeInTheDocument();
    expect(await screen.findByText(/first gene/i)).toBeInTheDocument();
  });

  it("renders species and genome version tags from the annotation fetch", async () => {
    mockAnnotation();
    renderGenePage();
    expect(
      await screen.findByText("Pinus sylvestris")
    ).toBeInTheDocument();
    expect(screen.getByText("Araport11")).toBeInTheDocument();
  });

  it("renders the remaining placeholder card headings", async () => {
    mockAnnotation();
    renderGenePage();
    expect(
      await screen.findByRole("heading", { name: /genome browser/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /best arabidopsis hit/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /best hits in other taxa/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /go terms/i })
    ).toBeInTheDocument();
  });

  it("renders a 'Back to My Lists' link pointing to '/'", async () => {
    mockAnnotation();
    renderGenePage();
    const link = await screen.findByRole("link", {
      name: /back to my lists/i,
    });
    expect(link).toHaveAttribute("href", "/");
  });

  it("shows only the gene id in the breadcrumb when there is no list referrer", async () => {
    mockAnnotation();
    renderGenePage();
    const nav = await screen.findByRole("navigation", {
      name: /breadcrumb/i,
    });
    expect(nav).toHaveTextContent(/My Lists\s*\/\s*AT1G01010/);
    expect(
      screen.queryByRole("link", { name: /drought-response tfs/i })
    ).not.toBeInTheDocument();
  });

  it("renders a chromosome tag in the header from the gene fetch", async () => {
    mockAnnotation();
    renderGenePage();
    const heading = await screen.findByRole("heading", { name: "AT1G01010" });
    const header = heading.closest("article");
    expect(header).not.toBeNull();
    const scoped = within(header as HTMLElement);
    expect(await scoped.findByText("Chr1")).toBeInTheDocument();
  });

  it("populates the Annotation details card with chromosome, position, and strand", async () => {
    mockAnnotation();
    renderGenePage();
    const heading = await screen.findByRole("heading", {
      name: /annotation details/i,
    });
    const card = heading.closest("section");
    expect(card).not.toBeNull();
    const scoped = within(card as HTMLElement);
    expect(await scoped.findByText("Chr1")).toBeInTheDocument();
    expect(scoped.getByText(/3,631/)).toBeInTheDocument();
    expect(scoped.getByText(/5,899/)).toBeInTheDocument();
    expect(scoped.getByText("+")).toBeInTheDocument();
    expect(scoped.queryByText(/coming soon/i)).not.toBeInTheDocument();
  });

  it("links the list name in the breadcrumb when history state carries list context", async () => {
    window.history.replaceState(
      { listId: "abc-123", listName: "Drought-response TFs" },
      ""
    );
    mockAnnotation();
    renderGenePage();
    const listLink = await screen.findByRole("link", {
      name: /drought-response tfs/i,
    });
    expect(listLink).toHaveAttribute("href", "/lists/abc-123");
  });
});
