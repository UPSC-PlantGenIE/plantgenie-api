import { describe, it, expect, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

  it("links each gene id to its gene page", async () => {
    server.use(
      http.get("http://localhost:8000/api/v2/lists/:listId", ({ params }) => {
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
      })
    );
    renderListPage();
    const link = await screen.findByRole("link", { name: /AT1G01010/ });
    expect(link).toHaveAttribute(
      "href",
      "/genes/arath-Araport11/AT1G01010"
    );
  });

  it("renders a Remove button for each member gene", async () => {
    server.use(
      http.get("http://localhost:8000/api/v2/lists/:listId", ({ params }) => {
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
      })
    );
    renderListPage();
    expect(
      await screen.findByRole("button", { name: /remove AT1G01010/i })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /remove AT1G01020/i })
    ).toBeInTheDocument();
  });

  it("PATCHes the list with removeGeneIds when Remove is confirmed", async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    server.use(
      http.get("http://localhost:8000/api/v2/lists/:listId", ({ params }) => {
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
      })
    );

    let patched: { removeGeneIds?: string[] } | null = null;
    server.use(
      http.patch(
        "http://localhost:8000/api/v2/lists/abc-123",
        async ({ request }) => {
          patched = (await request.json()) as { removeGeneIds?: string[] };
          return HttpResponse.json({ listId: "abc-123" });
        }
      )
    );

    renderListPage();
    await user.click(
      await screen.findByRole("button", { name: /remove AT1G01010/i })
    );

    await waitFor(() => {
      expect(patched).toEqual({ removeGeneIds: ["AT1G01010"] });
    });
    expect(confirmSpy).toHaveBeenCalled();
    confirmSpy.mockRestore();
  });

  it("does not PATCH when the Remove confirmation is cancelled", async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(false);
    server.use(
      http.get("http://localhost:8000/api/v2/lists/:listId", ({ params }) => {
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
      })
    );

    let patchCalled = false;
    server.use(
      http.patch("http://localhost:8000/api/v2/lists/abc-123", () => {
        patchCalled = true;
        return HttpResponse.json({ listId: "abc-123" });
      })
    );

    renderListPage();
    await user.click(
      await screen.findByRole("button", { name: /remove AT1G01010/i })
    );

    expect(confirmSpy).toHaveBeenCalled();
    expect(patchCalled).toBe(false);
    confirmSpy.mockRestore();
  });

  it("exports a TSV of gene IDs and descriptions when Export is clicked", async () => {
    const user = userEvent.setup();
    server.use(
      http.get("http://localhost:8000/api/v2/lists/:listId", ({ params }) => {
        return HttpResponse.json({
          listId: params.listId,
          name: "Stress Response",
          description: null,
          annotationId: "arath-Araport11",
          taxonName: "Arabidopsis thaliana",
          createdAt: "2026-04-14 12:00:00",
          geneCount: 2,
          memberGeneIds: ["AT1G01010", "AT1G01020"],
        });
      })
    );

    const blobs: Blob[] = [];
    const origCreate = URL.createObjectURL;
    const origRevoke = URL.revokeObjectURL;
    URL.createObjectURL = vi.fn((blob: Blob) => {
      blobs.push(blob);
      return "blob:mock-url";
    });
    URL.revokeObjectURL = vi.fn();
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {});

    renderListPage();
    await screen.findByText(/first gene/i);
    await screen.findByText(/second gene/i);
    await user.click(screen.getByRole("button", { name: /export/i }));

    expect(URL.createObjectURL).toHaveBeenCalledTimes(1);
    const text = await blobs[0].text();
    expect(text).toBe(
      "geneId\tdescription\nAT1G01010\tFirst gene\nAT1G01020\tSecond gene"
    );

    clickSpy.mockRestore();
    URL.createObjectURL = origCreate;
    URL.revokeObjectURL = origRevoke;
  });

  it("names the exported file using the list name slug and today's date", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-05-13T10:00:00Z"));
    const user = userEvent.setup();
    server.use(
      http.get("http://localhost:8000/api/v2/lists/:listId", ({ params }) => {
        return HttpResponse.json({
          listId: params.listId,
          name: "Stress Response!",
          description: null,
          annotationId: "arath-Araport11",
          taxonName: "Arabidopsis thaliana",
          createdAt: "2026-04-14 12:00:00",
          geneCount: 1,
          memberGeneIds: ["AT1G01010"],
        });
      })
    );

    const origCreate = URL.createObjectURL;
    const origRevoke = URL.revokeObjectURL;
    URL.createObjectURL = vi.fn(() => "blob:mock-url");
    URL.revokeObjectURL = vi.fn();
    let downloadName = "";
    const clickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(function (this: HTMLAnchorElement) {
        downloadName = this.download;
      });

    renderListPage();
    await screen.findByText("AT1G01010");
    await user.click(screen.getByRole("button", { name: /export/i }));

    expect(downloadName).toBe("stress-response-2026-05-13.tsv");

    clickSpy.mockRestore();
    URL.createObjectURL = origCreate;
    URL.revokeObjectURL = origRevoke;
    vi.useRealTimers();
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
