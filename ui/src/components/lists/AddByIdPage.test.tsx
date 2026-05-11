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
    expect(screen.getByText("UNKNOWN")).toBeInTheDocument();
  });

  it("renders each not-found gene id in its own row with an X indicator", async () => {
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

    await user.type(screen.getByRole("textbox"), "UNKNOWN1, UNKNOWN2");
    await user.click(screen.getByRole("button", { name: /validate/i }));

    const id1 = await screen.findByText("UNKNOWN1");
    const id2 = screen.getByText("UNKNOWN2");
    expect(id1.closest("li")).not.toBeNull();
    expect(id1.closest("li")).not.toBe(id2.closest("li"));

    const indicators = screen.getAllByLabelText(/not found/i);
    expect(indicators).toHaveLength(2);
  });

  it("renders a select-all checkbox when there are found genes", async () => {
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

    await user.type(screen.getByRole("textbox"), "AT1G01010, AT1G01020");
    await user.click(screen.getByRole("button", { name: /validate/i }));

    expect(
      await screen.findByRole("checkbox", { name: /select all/i })
    ).toBeInTheDocument();
  });

  it("toggles all found genes via the select-all checkbox", async () => {
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

    await user.type(screen.getByRole("textbox"), "AT1G01010, AT1G01020");
    await user.click(screen.getByRole("button", { name: /validate/i }));

    const selectAll = await screen.findByRole("checkbox", {
      name: /select all/i,
    });
    const gene1 = screen.getByRole("checkbox", { name: /AT1G01010/i });
    const gene2 = screen.getByRole("checkbox", { name: /AT1G01020/i });

    expect(gene1).toBeChecked();
    expect(gene2).toBeChecked();

    await user.click(selectAll);
    expect(gene1).not.toBeChecked();
    expect(gene2).not.toBeChecked();

    await user.click(selectAll);
    expect(gene1).toBeChecked();
    expect(gene2).toBeChecked();
  });

  it("shows indeterminate state when some but not all found genes are selected", async () => {
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

    await user.type(screen.getByRole("textbox"), "AT1G01010, AT1G01020");
    await user.click(screen.getByRole("button", { name: /validate/i }));

    const gene1 = await screen.findByRole("checkbox", {
      name: /AT1G01010/i,
    });
    await user.click(gene1);

    const selectAll = screen.getByRole("checkbox", { name: /select all/i });
    expect(selectAll).toBePartiallyChecked();
  });

  it("preserves the input order across found and not-found rows", async () => {
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

    await user.type(
      screen.getByRole("textbox"),
      "UNKNOWN1, AT1G01010, UNKNOWN2"
    );
    await user.click(screen.getByRole("button", { name: /validate/i }));

    await screen.findByText("UNKNOWN1");
    const rows = screen.getAllByRole("listitem");
    expect(rows).toHaveLength(3);
    expect(rows[0]).toHaveTextContent("UNKNOWN1");
    expect(rows[1]).toHaveTextContent("AT1G01010");
    expect(rows[2]).toHaveTextContent("UNKNOWN2");
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
