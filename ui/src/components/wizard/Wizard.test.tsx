import { describe, it, expect } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithStore } from "../../test-utils";
import Wizard from "./Wizard";
import { memoryLocation } from "wouter/memory-location";
import { Router } from "wouter";

describe("Wizard", () => {
  it("starts on the taxon step with Continue disabled", async () => {
    renderWithStore(<Wizard />);
    expect(
      screen.getByRole("heading", { name: /select a taxon/i })
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /continue/i })).toBeDisabled();
    expect(await screen.findAllByRole("radio")).toHaveLength(2);
  });

  it("offers no Back button on the taxon step", () => {
    renderWithStore(<Wizard />);
    expect(
      screen.queryByRole("button", { name: /back/i })
    ).not.toBeInTheDocument();
  });

  it("advances to the genome step when Continue is clicked", async () => {
    const user = userEvent.setup();
    renderWithStore(<Wizard />, {
      preloadedState: {
        wizard: {
          step: 1,
          name: "",
          description: "",
          taxonId: "pinsy",
          annotationId: null,
        },
      },
    });
    await user.click(screen.getByRole("button", { name: /continue/i }));
    expect(
      screen.getByRole("heading", { name: /select a genome/i })
    ).toBeInTheDocument();
  });

  it("advances from the genome step to the list details step", async () => {
    const user = userEvent.setup();
    renderWithStore(<Wizard />, {
      preloadedState: {
        wizard: {
          step: 2,
          name: "",
          description: "",
          taxonId: "pinsy",
          annotationId: "pinsy-Araport11",
        },
      },
    });
    const continueButton = screen.getByRole("button", { name: /continue/i });
    await waitFor(() => expect(continueButton).toBeEnabled());
    await user.click(continueButton);
    expect(
      screen.getByRole("heading", { name: /name your list/i })
    ).toBeInTheDocument();
  });

  it("Back on the genome step returns to the taxon step", async () => {
    const user = userEvent.setup();
    renderWithStore(<Wizard />, {
      preloadedState: {
        wizard: {
          step: 2,
          name: "",
          description: "",
          taxonId: "pinsy",
          annotationId: null,
        },
      },
    });
    await user.click(screen.getByRole("button", { name: /back/i }));
    expect(
      screen.getByRole("heading", { name: /select a taxon/i })
    ).toBeInTheDocument();
  });

  it("Back on the list details step returns to the genome step with the name preserved", async () => {
    const user = userEvent.setup();
    renderWithStore(<Wizard />, {
      preloadedState: {
        wizard: {
          step: 3,
          name: "My list",
          description: "",
          taxonId: "pinsy",
          annotationId: "pinsy-Araport11",
        },
      },
    });
    await user.click(screen.getByRole("button", { name: /back/i }));
    expect(
      screen.getByRole("heading", { name: /select a genome/i })
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/list name/i)).toHaveValue("My list");
  });

  it("the list details step shows the chosen taxon and genome, and a Create list button", async () => {
    renderWithStore(<Wizard />, {
      preloadedState: {
        wizard: {
          step: 3,
          name: "My list",
          description: "",
          taxonId: "pinsy",
          annotationId: "pinsy-Araport11",
        },
      },
    });
    expect(
      await screen.findByText(
        /new gene list.*pinus sylvestris.*v2\.0.*araport11/i
      )
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create list/i })
    ).toBeInTheDocument();
  });

  it("Create list is disabled until the list has a name", async () => {
    const user = userEvent.setup();
    renderWithStore(<Wizard />, {
      preloadedState: {
        wizard: {
          step: 3,
          name: "",
          description: "",
          taxonId: "pinsy",
          annotationId: "pinsy-Araport11",
        },
      },
    });
    expect(screen.getByRole("button", { name: /create list/i })).toBeDisabled();
    await user.type(screen.getByLabelText(/list name/i), "My list");
    expect(screen.getByRole("button", { name: /create list/i })).toBeEnabled();
  });

  it("clicking Create list POSTs and navigates to the new list", async () => {
    const { hook, history } = memoryLocation({ path: "/", record: true });

    const user = userEvent.setup();

    renderWithStore(
      <Router hook={hook}>
        <Wizard />
      </Router>,
      {
        preloadedState: {
          wizard: {
            step: 3,
            name: "My list",
            description: "",
            taxonId: "pinsy",
            annotationId: "pinsy-Araport11",
          },
        },
      }
    );

    const createButton = await screen.findByRole("button", {
      name: /create list/i,
    });
    await waitFor(() => expect(createButton).toBeEnabled());
    await user.click(createButton);

    await waitFor(() => {
      expect(history?.at(-1)).toBe("/lists/fake-list-123");
    });
  });

  it("resets wizard state after a successful create so a fresh visit starts at step 1", async () => {
    const { hook } = memoryLocation({ path: "/lists/new" });
    const user = userEvent.setup();
    const { store } = renderWithStore(
      <Router hook={hook}>
        <Wizard />
      </Router>,
      {
        preloadedState: {
          wizard: {
            step: 3,
            name: "My list",
            description: "old description",
            taxonId: "pinsy",
            annotationId: "pinsy-Araport11",
          },
        },
      }
    );

    const createButton = await screen.findByRole("button", {
      name: /create list/i,
    });
    await waitFor(() => expect(createButton).toBeEnabled());
    await user.click(createButton);

    await waitFor(() => {
      expect(store.getState().wizard.step).toBe(1);
    });
    expect(store.getState().wizard.name).toBe("");
    expect(store.getState().wizard.description).toBe("");
    expect(store.getState().wizard.taxonId).toBeNull();
    expect(store.getState().wizard.annotationId).toBeNull();
  });

  it("Continue on the taxon step is disabled until a taxon is picked", async () => {
    const user = userEvent.setup();
    renderWithStore(<Wizard />);
    expect(screen.getByRole("button", { name: /continue/i })).toBeDisabled();
    await user.click(
      await screen.findByRole("radio", { name: /pinus sylvestris/i })
    );
    expect(screen.getByRole("button", { name: /continue/i })).toBeEnabled();
  });
});
