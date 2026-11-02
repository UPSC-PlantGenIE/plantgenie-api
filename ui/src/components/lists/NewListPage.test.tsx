import { describe, it, expect } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { Router } from "wouter";
import { memoryLocation } from "wouter/memory-location";
import App from "../../App";
import { server } from "../../mocks/server";
import { renderWithStore } from "../../test-utils";

const renderNewList = () => {
  const { hook, history } = memoryLocation({
    path: "/lists/new",
    record: true,
  });

  const utils = renderWithStore(
    <Router hook={hook}>
      <App />
    </Router>,
    { preloadedState: { account: { accountId: "1234567890123456" } } }
  );

  return { ...utils, history };
};

describe("NewListPage", () => {
  it("shows every choice on one page", async () => {
    renderNewList();

    expect(
      screen.getByRole("heading", { name: /new gene list/i })
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("radio", { name: /pinus sylvestris/i })
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/list name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /create list/i })).toBeDisabled();
    expect(screen.queryByRole("button", { name: /continue/i })).toBeNull();
  });

  it("asks for a taxon before offering genomes", async () => {
    renderNewList();

    expect(await screen.findAllByRole("radio")).toHaveLength(2);
    expect(screen.getByText(/pick a taxon/i)).toBeInTheDocument();
  });

  it("offers the picked taxon's genomes with the default selected", async () => {
    const user = userEvent.setup();
    renderNewList();

    await user.click(
      await screen.findByRole("radio", { name: /pinus sylvestris/i })
    );

    expect(
      await screen.findByRole("radio", { name: /araport11/i })
    ).toBeChecked();
    expect(screen.getByRole("radio", { name: /tair10/i })).not.toBeChecked();
    expect(screen.queryByText(/pick a taxon/i)).toBeNull();
  });

  it("selects the new default when the taxon changes", async () => {
    const user = userEvent.setup();
    renderNewList();

    await user.click(
      await screen.findByRole("radio", { name: /pinus sylvestris/i })
    );
    await user.click(await screen.findByRole("radio", { name: /tair10/i }));
    await user.click(screen.getByRole("radio", { name: /picea abies/i }));

    expect(
      await screen.findByRole("radio", { name: /annotation - v1/i })
    ).toBeChecked();
    expect(screen.queryByRole("radio", { name: /tair10/i })).toBeNull();
  });

  it("disables Create list until a genome and a name are chosen", async () => {
    const user = userEvent.setup();
    renderNewList();

    await user.type(screen.getByLabelText(/list name/i), "My list");
    expect(screen.getByRole("button", { name: /create list/i })).toBeDisabled();

    await user.click(
      await screen.findByRole("radio", { name: /pinus sylvestris/i })
    );
    await screen.findByRole("radio", { name: /araport11/i });

    expect(screen.getByRole("button", { name: /create list/i })).toBeEnabled();
  });

  it("creates the list with the chosen values and goes to it", async () => {
    let body: unknown;
    server.use(
      http.post("http://localhost:8000/api/v2/lists", async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ listId: "fake-list-123" });
      })
    );
    const user = userEvent.setup();
    const { history } = renderNewList();

    await user.click(
      await screen.findByRole("radio", { name: /pinus sylvestris/i })
    );
    await user.click(await screen.findByRole("radio", { name: /tair10/i }));
    await user.type(screen.getByLabelText(/list name/i), "My list");
    await user.type(screen.getByLabelText(/description/i), "Some notes");
    await user.click(screen.getByRole("button", { name: /create list/i }));

    await waitFor(() => expect(history.at(-1)).toBe("/lists/fake-list-123"));
    expect(body).toEqual({
      name: "My list",
      description: "Some notes",
      annotationId: "pinsy-TAIR10",
      taxonName: "Pinus sylvestris",
    });
  });

  it("clears the form when the user leaves and comes back", async () => {
    const user = userEvent.setup();
    renderNewList();

    await user.click(
      await screen.findByRole("radio", { name: /pinus sylvestris/i })
    );
    await user.type(screen.getByLabelText(/list name/i), "My list");
    await user.click(screen.getByRole("link", { name: "Lists" }));
    await user.click(
      (await screen.findAllByRole("link", { name: /new list/i }))[0]
    );

    expect(
      await screen.findByRole("radio", { name: /pinus sylvestris/i })
    ).not.toBeChecked();
    expect(screen.getByLabelText(/list name/i)).toHaveValue("");
  });

  it("reports when taxa cannot be loaded", async () => {
    server.use(
      http.get("http://localhost:8000/api/v2/taxa", () => HttpResponse.error())
    );
    renderNewList();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /couldn't load taxa/i
    );
  });

  it("reports when genomes cannot be loaded", async () => {
    server.use(
      http.get("http://localhost:8000/api/v2/annotations", () =>
        HttpResponse.error()
      )
    );
    const user = userEvent.setup();
    renderNewList();

    await user.click(
      await screen.findByRole("radio", { name: /pinus sylvestris/i })
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /couldn't load genomes/i
    );
  });
});
