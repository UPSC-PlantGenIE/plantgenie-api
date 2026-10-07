import { describe, it, expect } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { server } from "../../../mocks/server";
import { renderWithStore } from "../../../test-utils";
import ListName from "./ListName";

describe("ListName", () => {
  const wizardFor = (taxonId: string | null) => ({
    wizard: {
      step: 3 as const,
      name: "",
      description: "",
      taxonId,
      annotationId: null,
    },
  });

  const mockLists = (lists: object[]) =>
    server.use(
      http.get("http://localhost:8000/api/v2/lists", () =>
        HttpResponse.json({ lists })
      )
    );

  it("suggests the default title for the selected species", async () => {
    mockLists([]);
    renderWithStore(<ListName />, { preloadedState: wizardFor("picab") });
    await waitFor(() =>
      expect(screen.getByLabelText(/list name/i)).toHaveAttribute(
        "placeholder",
        "e.g. Drought resistance genes in Picea abies"
      )
    );
  });

  it("reuses the topic of the last list when the species differs", async () => {
    mockLists([
      {
        listId: "1",
        name: "dehydration in Pinus sylvestris",
        description: null,
        annotationId: "pinsy-v2.0",
        taxonName: "Pinus sylvestris",
        createdAt: "2026-05-01T12:00:00",
        geneCount: 3,
      },
    ]);
    renderWithStore(<ListName />, { preloadedState: wizardFor("picab") });
    await waitFor(() =>
      expect(screen.getByLabelText(/list name/i)).toHaveAttribute(
        "placeholder",
        "e.g. dehydration in Picea abies"
      )
    );
  });

  it("ignores the last list's name when it isn't '<something> in <species>'", async () => {
    mockLists([
      {
        listId: "1",
        name: "My favourites",
        description: null,
        annotationId: "pinsy-v2.0",
        taxonName: "Pinus sylvestris",
        createdAt: "2026-05-01T12:00:00",
        geneCount: 3,
      },
    ]);
    renderWithStore(<ListName />, { preloadedState: wizardFor("picab") });
    await waitFor(() =>
      expect(screen.getByLabelText(/list name/i)).toHaveAttribute(
        "placeholder",
        "e.g. Drought resistance genes in Picea abies"
      )
    );
  });

  it("keeps the default topic when the species matches the last list", async () => {
    mockLists([
      {
        listId: "1",
        name: "dehydration in Pinus sylvestris",
        description: null,
        annotationId: "pinsy-v2.0",
        taxonName: "Pinus sylvestris",
        createdAt: "2026-05-01T12:00:00",
        geneCount: 3,
      },
    ]);
    renderWithStore(<ListName />, { preloadedState: wizardFor("pinsy") });
    await waitFor(() =>
      expect(screen.getByLabelText(/list name/i)).toHaveAttribute(
        "placeholder",
        "e.g. Drought resistance genes in Pinus sylvestris"
      )
    );
  });

  it("pressing Tab in the empty input fills in the suggestion", async () => {
    mockLists([]);
    const user = userEvent.setup();
    const { store } = renderWithStore(<ListName />, {
      preloadedState: wizardFor("picab"),
    });
    const input = screen.getByLabelText(/list name/i);
    await waitFor(() =>
      expect(input).toHaveAttribute(
        "placeholder",
        expect.stringContaining("Picea")
      )
    );
    await user.click(input);
    await user.tab();
    expect(store.getState().wizard.name).toBe(
      "Drought resistance genes in Picea abies"
    );
    expect(input).toHaveFocus();
  });

  it("Tab does not overwrite a name the user already typed", async () => {
    const user = userEvent.setup();
    const { store } = renderWithStore(<ListName />, {
      preloadedState: wizardFor("picab"),
    });
    await user.type(screen.getByLabelText(/list name/i), "Mine");
    await user.tab();
    expect(store.getState().wizard.name).toBe("Mine");
  });

  it("renders the description textarea", () => {
    renderWithStore(<ListName />);
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
  });

  it("reflects initial store state in the inputs", () => {
    renderWithStore(<ListName />, {
      preloadedState: {
        wizard: {
          step: 3,
          name: "Existing list",
          description: "Already typed",
          taxonId: null,
          annotationId: null,
        },
      },
    });
    expect(screen.getByLabelText(/list name/i)).toHaveValue("Existing list");
    expect(screen.getByLabelText(/description/i)).toHaveValue("Already typed");
  });

  it("typing in list name updates the store", async () => {
    const user = userEvent.setup();
    const { store } = renderWithStore(<ListName />);
    await user.type(screen.getByLabelText(/list name/i), "My list");
    expect(store.getState().wizard.name).toBe("My list");
  });

  it("typing in description updates the store", async () => {
    const user = userEvent.setup();
    const { store } = renderWithStore(<ListName />);
    await user.type(
      screen.getByLabelText(/description/i),
      "Notes about the list"
    );
    expect(store.getState().wizard.description).toBe("Notes about the list");
  });
});
