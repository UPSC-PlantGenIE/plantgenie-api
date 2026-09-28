import { describe, it, expect, beforeEach, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { Route, Router } from "wouter";
import { memoryLocation } from "wouter/memory-location";
import { server } from "../../mocks/server";
import { renderWithStore } from "../../test-utils";
import HeatmapPage from "./HeatmapPage";

const renderHeatmapPage = (path = "/lists/abc-123/heatmap") => {
  const { hook } = memoryLocation({ path });
  return renderWithStore(
    <Router hook={hook}>
      <Route path="/lists/:listId/heatmap" component={HeatmapPage} />
    </Router>
  );
};

const mockPopulatedList = () =>
  server.use(
    http.get(
      "http://localhost:8000/api/v2/lists/:listId",
      ({ params }) => {
        return HttpResponse.json({
          listId: params.listId,
          name: "Cellulose synthases",
          description: null,
          annotationId: "picab-v2.0",
          taxonName: "Picea abies",
          createdAt: "2026-04-14 12:00:00",
          geneCount: 2,
          memberGeneIds: ["PA_chr01_G000102", "PA_chr01_G000106"],
        });
      }
    )
  );

describe("HeatmapPage", () => {
  beforeEach(() => {
    localStorage.clear();
    mockPopulatedList();
  });

  it("shows the experiment and its samples", async () => {
    renderHeatmapPage();
    expect(
      await screen.findByRole("option", { name: /picab cold roots/i })
    ).toBeInTheDocument();
    expect(await screen.findByText("control-1")).toBeInTheDocument();
  });

  it("names the genes that have no data in this experiment", async () => {
    renderHeatmapPage();
    expect(
      await screen.findByText(/no data in this experiment/i)
    ).toBeInTheDocument();
    expect(
      await screen.findByText("PA_chr01_G000106")
    ).toBeInTheDocument();
  });

  it("offers PNG, SVG and TSV exports", async () => {
    const user = userEvent.setup();
    renderHeatmapPage();
    await screen.findByText("control-1");
    await user.click(await screen.findByRole("button", { name: /export/i }));
    expect(
      screen.getByRole("menuitem", { name: /png/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("menuitem", { name: /svg/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("menuitem", { name: /tsv/i })
    ).toBeInTheDocument();
  });

  it("exports the matrix as TSV with raw values", async () => {
    const user = userEvent.setup();
    const blobs: Blob[] = [];
    const originalCreate = URL.createObjectURL;
    const originalRevoke = URL.revokeObjectURL;
    URL.createObjectURL = vi.fn((blob: Blob) => {
      blobs.push(blob);
      return "blob:mock-url";
    });
    URL.revokeObjectURL = vi.fn();
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {});

    renderHeatmapPage();
    await screen.findByText("control-1");
    await user.click(await screen.findByRole("button", { name: /export/i }));
    await user.click(screen.getByRole("menuitem", { name: /tsv/i }));

    expect(await blobs[0].text()).toBe(
      "geneId\tcontrol-1\tcold-1\nPA_chr01_G000102\t0\t10"
    );

    clickSpy.mockRestore();
    URL.createObjectURL = originalCreate;
    URL.revokeObjectURL = originalRevoke;
  });

  it("exports the heatmap as an SVG file", async () => {
    const user = userEvent.setup();
    const blobs: Blob[] = [];
    const originalCreate = URL.createObjectURL;
    const originalRevoke = URL.revokeObjectURL;
    URL.createObjectURL = vi.fn((blob: Blob) => {
      blobs.push(blob);
      return "blob:mock-url";
    });
    URL.revokeObjectURL = vi.fn();
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {});

    renderHeatmapPage();
    await screen.findByText("control-1");
    await user.click(await screen.findByRole("button", { name: /export/i }));
    await user.click(screen.getByRole("menuitem", { name: /svg/i }));

    const text = await blobs[0].text();
    expect(text).toContain("<svg");
    expect(text).toContain("PA_chr01_G000102");

    clickSpy.mockRestore();
    URL.createObjectURL = originalCreate;
    URL.revokeObjectURL = originalRevoke;
  });

  it("remembers the chosen experiment per annotation", async () => {
    renderHeatmapPage();
    await screen.findByRole("option", { name: /picab cold roots/i });
    await waitFor(() =>
      expect(
        localStorage.getItem("heatmap-experiment-picab-v2.0")
      ).toEqual("picab-v2.0-cold-roots")
    );
  });
});
