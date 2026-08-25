import { describe, it, expect, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

  it("renders each list with name, description, taxon, genome version, gene count, and formatted date", async () => {
    server.use(
      http.get("http://localhost:8000/api/v2/lists", () =>
        HttpResponse.json({
          lists: [
            {
              listId: "abc-123",
              name: "Drought-response TFs",
              description: "Transcription factors involved in drought",
              annotationId: "arath-Araport11",
              taxonName: "Arabidopsis thaliana",
              createdAt: "2026-04-14T12:00:00",
              geneCount: 42,
            },
          ],
        })
      )
    );
    renderWithStore(<MyListsPage />);

    expect(
      await screen.findByText("Drought-response TFs")
    ).toBeInTheDocument();
    expect(
      screen.getByText(/transcription factors involved in drought/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Arabidopsis thaliana")).toBeInTheDocument();
    expect(screen.getByText("Araport11")).toBeInTheDocument();
    expect(screen.getByText(/42/)).toBeInTheDocument();
    expect(screen.getByText("Apr 14, 2026")).toBeInTheDocument();
  });

  it("shows the total list count in the footer", async () => {
    server.use(
      http.get("http://localhost:8000/api/v2/lists", () =>
        HttpResponse.json({
          lists: [
            {
              listId: "1",
              name: "A",
              description: null,
              annotationId: "arath-Araport11",
              taxonName: "Arabidopsis thaliana",
              createdAt: "2026-01-01T00:00:00",
              geneCount: 0,
            },
            {
              listId: "2",
              name: "B",
              description: null,
              annotationId: "arath-Araport11",
              taxonName: "Arabidopsis thaliana",
              createdAt: "2026-01-01T00:00:00",
              geneCount: 0,
            },
            {
              listId: "3",
              name: "C",
              description: null,
              annotationId: "arath-Araport11",
              taxonName: "Arabidopsis thaliana",
              createdAt: "2026-01-01T00:00:00",
              geneCount: 0,
            },
          ],
        })
      )
    );
    renderWithStore(<MyListsPage />);

    expect(await screen.findByText(/3 lists total/i)).toBeInTheDocument();
  });

  it("links each row to /lists/:listId", async () => {
    renderWithStore(<MyListsPage />);
    const link = await screen.findByRole("link", { name: /test list/i });
    expect(link).toHaveAttribute("href", "/lists/abc-123");
  });

  it("renders a + New list button linking to /lists/new", () => {
    renderWithStore(<MyListsPage />);
    const link = screen.getByRole("link", { name: /\+ new list/i });
    expect(link).toHaveAttribute("href", "/lists/new");
  });

  it("renders a Delete button for each list", async () => {
    renderWithStore(<MyListsPage />);
    expect(
      await screen.findByRole("button", { name: /delete test list/i })
    ).toBeInTheDocument();
  });

  it("calls DELETE /v2/lists/:listId when Delete is confirmed", async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);

    let deletedId: string | null = null;
    server.use(
      http.delete(
        "http://localhost:8000/api/v2/lists/:listId",
        ({ params }) => {
          deletedId = params.listId as string;
          return new HttpResponse(null, { status: 204 });
        }
      )
    );

    renderWithStore(<MyListsPage />);
    await user.click(
      await screen.findByRole("button", { name: /delete test list/i })
    );

    await waitFor(() => {
      expect(deletedId).toBe("abc-123");
    });
    expect(confirmSpy).toHaveBeenCalled();
    confirmSpy.mockRestore();
  });

  it("does not call DELETE when the confirm is cancelled", async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(false);

    let deleteCalled = false;
    server.use(
      http.delete("http://localhost:8000/api/v2/lists/:listId", () => {
        deleteCalled = true;
        return new HttpResponse(null, { status: 204 });
      })
    );

    renderWithStore(<MyListsPage />);
    await user.click(
      await screen.findByRole("button", { name: /delete test list/i })
    );

    expect(confirmSpy).toHaveBeenCalled();
    expect(deleteCalled).toBe(false);
    confirmSpy.mockRestore();
  });

  it("removes the deleted list from the page after success", async () => {
    const user = userEvent.setup();
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);

    let lists: GeneList[] = [
      {
        listId: "abc-123",
        name: "Doomed list",
        description: null,
        annotationId: "arath-Araport11",
        taxonName: "Arabidopsis thaliana",
        createdAt: "2026-04-14T12:00:00",
        geneCount: 0,
      },
    ];
    server.use(
      http.get("http://localhost:8000/api/v2/lists", () =>
        HttpResponse.json({ lists })
      ),
      http.delete("http://localhost:8000/api/v2/lists/:listId", () => {
        lists = [];
        return new HttpResponse(null, { status: 204 });
      })
    );

    renderWithStore(<MyListsPage />);
    await user.click(
      await screen.findByRole("button", { name: /delete doomed list/i })
    );

    await waitFor(() => {
      expect(screen.queryByText("Doomed list")).not.toBeInTheDocument();
    });
    confirmSpy.mockRestore();
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
