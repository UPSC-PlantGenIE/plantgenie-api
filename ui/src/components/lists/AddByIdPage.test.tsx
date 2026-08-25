import { describe, it, expect } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { Route, Router } from "wouter";
import { memoryLocation } from "wouter/memory-location";
import { server } from "../../mocks/server";
import { renderWithStore } from "../../test-utils";
import AddByIdPage from "./AddByIdPage";
import ListPage from "./ListPage";

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

  it("renders each not-found gene id in its own row", async () => {
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

    const notFoundRegion = await screen.findByRole("region", {
      name: /not found/i,
    });
    const rows = within(notFoundRegion).getAllByRole("listitem");
    expect(rows).toHaveLength(2);
    expect(rows[0]).toHaveTextContent("UNKNOWN1");
    expect(rows[1]).toHaveTextContent("UNKNOWN2");
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

  it("splits valid and not-found genes into separate accessible regions", async () => {
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
      "AT1G01010, UNKNOWN1, AT1G01020, UNKNOWN2"
    );
    await user.click(screen.getByRole("button", { name: /validate/i }));

    const validRegion = await screen.findByRole("region", {
      name: /valid genes/i,
    });
    const notFoundRegion = screen.getByRole("region", { name: /not found/i });

    expect(within(validRegion).getByText(/AT1G01010/)).toBeInTheDocument();
    expect(within(validRegion).getByText(/AT1G01020/)).toBeInTheDocument();
    expect(within(validRegion).queryByText("UNKNOWN1")).not.toBeInTheDocument();
    expect(within(validRegion).queryByText("UNKNOWN2")).not.toBeInTheDocument();

    expect(within(notFoundRegion).getByText("UNKNOWN1")).toBeInTheDocument();
    expect(within(notFoundRegion).getByText("UNKNOWN2")).toBeInTheDocument();
    expect(
      within(notFoundRegion).queryByText(/AT1G01010/)
    ).not.toBeInTheDocument();
    expect(
      within(notFoundRegion).queryByText(/AT1G01020/)
    ).not.toBeInTheDocument();
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

    await user.click(screen.getByRole("button", { name: /add .* to list/i }));

    await waitFor(() => {
      expect(patched).toEqual({ addGeneIds: ["AT1G01010"] });
    });
    await waitFor(() => {
      expect(history?.at(-1)).toBe("/lists/abc-123");
    });
  });

  it("shows added genes on the list page after navigating back", async () => {
    const user = userEvent.setup();
    const { hook } = memoryLocation({
      path: "/lists/abc-123/genes/add-by-id",
    });

    const listMembers: string[] = [];
    server.use(
      http.get(
        "http://localhost:8000/api/v2/lists/:listId",
        ({ params }) =>
          HttpResponse.json({
            listId: params.listId,
            name: "Test list",
            description: null,
            annotationId: "arath-Araport11",
            taxonName: "Arabidopsis thaliana",
            createdAt: "2026-04-14 12:00:00",
            geneCount: listMembers.length,
            memberGeneIds: [...listMembers],
          })
      ),
      http.patch(
        "http://localhost:8000/api/v2/lists/:listId",
        async ({ request, params }) => {
          const body = (await request.json()) as { addGeneIds?: string[] };
          if (body.addGeneIds) listMembers.push(...body.addGeneIds);
          return HttpResponse.json({ listId: params.listId });
        }
      )
    );

    renderWithStore(
      <Router hook={hook}>
        <Route
          path="/lists/:listId/genes/add-by-id"
          component={AddByIdPage}
        />
        <Route path="/lists/:listId" component={ListPage} />
      </Router>
    );

    await user.type(screen.getByRole("textbox"), "AT1G01010");
    await user.click(screen.getByRole("button", { name: /validate/i }));
    await screen.findByRole("checkbox", { name: /AT1G01010/i });
    await user.click(screen.getByRole("button", { name: /add .* to list/i }));

    expect(
      await screen.findByRole("heading", { name: /test list/i })
    ).toBeInTheDocument();
    expect(await screen.findByText("AT1G01010")).toBeInTheDocument();
  });
});
