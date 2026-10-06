import { describe, it, expect } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { Router } from "wouter";
import { memoryLocation } from "wouter/memory-location";
import { server } from "../../mocks/server";
import { renderWithStore } from "../../test-utils";
import SemanticSearchButton from "./SemanticSearchButton";

const SPECIES_URL = "http://localhost:8000/api/v2/semantic-search/species";

const renderButton = (taxonName: string) => {
  server.use(
    http.get(SPECIES_URL, () =>
      HttpResponse.json([
        { abbreviation: "potra", scientificName: "Populus tremula" },
      ])
    )
  );
  const { hook } = memoryLocation({ path: "/lists/abc-123" });
  return renderWithStore(
    <Router hook={hook}>
      <SemanticSearchButton
        listId="abc-123"
        taxonName={taxonName}
        className="btn"
      />
    </Router>
  );
};

describe("SemanticSearchButton", () => {
  it("links to the search page for a supported species", async () => {
    renderButton("Populus tremula");
    await waitFor(() =>
      expect(
        screen.getByRole("link", { name: /search genes/i })
      ).toHaveAttribute("href", "/lists/abc-123/search")
    );
    expect(
      screen.getByRole("link", { name: /search genes/i })
    ).not.toHaveAttribute("aria-disabled");
  });

  it("is dimmed with a tooltip for an unsupported species", async () => {
    renderButton("Pinus contorta");
    const button = screen.getByRole("link", { name: /search genes/i });
    expect(button).toHaveAttribute("aria-disabled", "true");
    expect(button).toHaveAttribute("title", "Not applicable yet");
    expect(button).not.toHaveAttribute("href");
  });
});
