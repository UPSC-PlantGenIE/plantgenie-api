import { describe, it, expect } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { Route, Router } from "wouter";
import { memoryLocation } from "wouter/memory-location";
import { server } from "../../mocks/server";
import { renderWithStore } from "../../test-utils";
import AddByIdPage from "./AddByIdPage";

describe("AddByIdPage", () => {
  it("renders a textarea for gene ids and a Validate button", () => {
    renderWithStore(<AddByIdPage />);
    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /validate/i })
    ).toBeInTheDocument();
  });

  it("validates entered gene ids and shows found/notFound", async () => {
    const user = userEvent.setup();
    const { hook } = memoryLocation({
      path: "/lists/abc-123/genes/add-by-id",
    });
    renderWithStore(
      <Router hook={hook}>
        <Route
          path="/lists/:listId/genes/add-by-id"
          component={AddByIdPage}
        />
      </Router>
    );

    await user.type(screen.getByRole("textbox"), "AT1G01010,UNKNOWN");
    await user.click(screen.getByRole("button", { name: /validate/i }));

    expect(await screen.findByText(/GENE1/i)).toBeInTheDocument();
    expect(
      screen.getByText(/not found:.*UNKNOWN/i)
    ).toBeInTheDocument();
  });

  it("renders a checked checkbox for each found gene", async () => {
    const user = userEvent.setup();
    const { hook } = memoryLocation({
      path: "/lists/abc-123/genes/add-by-id",
    });
    renderWithStore(
      <Router hook={hook}>
        <Route
          path="/lists/:listId/genes/add-by-id"
          component={AddByIdPage}
        />
      </Router>
    );

    await user.type(screen.getByRole("textbox"), "AT1G01010");
    await user.click(screen.getByRole("button", { name: /validate/i }));

    const checkbox = await screen.findByRole("checkbox", {
      name: /AT1G01010/i,
    });
    expect(checkbox).toBeChecked();
  });

  it("adds checked genes to the list and navigates back", async () => {
    const user = userEvent.setup();
    const { hook, history } = memoryLocation({
      path: "/lists/abc-123/genes/add-by-id",
      record: true,
    });

    let patched: { addGeneIds?: string[] } | null = null;
    server.use(
      http.patch(
        "http://localhost:8000/api/v2/lists/abc-123",
        async ({ request }) => {
          patched = (await request.json()) as { addGeneIds?: string[] };
          return HttpResponse.json({ listId: "abc-123" });
        }
      )
    );

    renderWithStore(
      <Router hook={hook}>
        <Route
          path="/lists/:listId/genes/add-by-id"
          component={AddByIdPage}
        />
      </Router>
    );

    await user.type(screen.getByRole("textbox"), "AT1G01010");
    await user.click(screen.getByRole("button", { name: /validate/i }));
    await screen.findByRole("checkbox", { name: /AT1G01010/i });

    await user.click(screen.getByRole("button", { name: /add to list/i }));

    await waitFor(() => {
      expect(patched).toEqual({ addGeneIds: ["AT1G01010"] });
    });
    await waitFor(() => {
      expect(history?.at(-1)).toBe("/lists/abc-123");
    });
  });
});
