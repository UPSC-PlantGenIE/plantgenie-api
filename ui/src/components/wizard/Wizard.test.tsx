import { describe, it, expect } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Router } from "wouter";
import { memoryLocation } from "wouter/memory-location";
import App from "../../App";
import type { WizardState } from "../../store/wizardSlice";
import { renderWithStore } from "../../test-utils";

const emptyWizard: WizardState = {
  name: "",
  description: "",
  taxonId: null,
  annotationId: null,
};

const taxonChosen: WizardState = { ...emptyWizard, taxonId: "pinsy" };

const genomeChosen: WizardState = {
  ...taxonChosen,
  annotationId: "pinsy-Araport11",
};

const renderWizard = (path: string, wizard: WizardState = emptyWizard) => {
  const { hook, history } = memoryLocation({ path, record: true });

  const utils = renderWithStore(
    <Router hook={hook}>
      <App />
    </Router>,
    {
      preloadedState: {
        account: { accountId: "1234567890123456" },
        wizard,
      },
    }
  );

  return { ...utils, history };
};

describe("Wizard", () => {
  it("starts on the taxon step with Continue disabled", async () => {
    renderWizard("/lists/new");

    expect(
      screen.getByRole("heading", { name: /select a taxon/i })
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /continue/i })).toBeDisabled();
    expect(await screen.findAllByRole("radio")).toHaveLength(2);
  });

  it("shows only the current step", () => {
    renderWizard("/lists/new");

    expect(
      screen.queryByRole("heading", { name: /select a genome/i, hidden: true })
    ).toBeNull();
    expect(
      screen.queryByRole("heading", { name: /name your list/i, hidden: true })
    ).toBeNull();
  });

  it("offers no Back button on the taxon step", () => {
    renderWizard("/lists/new");

    expect(screen.queryByRole("button", { name: /back/i })).toBeNull();
  });

  it("enables Continue on the taxon step once a taxon is picked", async () => {
    const user = userEvent.setup();
    renderWizard("/lists/new");

    expect(screen.getByRole("button", { name: /continue/i })).toBeDisabled();
    await user.click(
      await screen.findByRole("radio", { name: /pinus sylvestris/i })
    );
    expect(screen.getByRole("button", { name: /continue/i })).toBeEnabled();
  });

  it("moves to the genome URL when Continue is clicked", async () => {
    const user = userEvent.setup();
    const { history } = renderWizard("/lists/new", taxonChosen);

    const continueButton = screen.getByRole("button", { name: /continue/i });
    await waitFor(() => expect(continueButton).toBeEnabled());
    await user.click(continueButton);

    expect(
      screen.getByRole("heading", { name: /select a genome/i })
    ).toBeInTheDocument();
    expect(history.at(-1)).toBe("/lists/new/genome");
  });

  it("moves from the genome step to the details URL", async () => {
    const user = userEvent.setup();
    const { history } = renderWizard("/lists/new/genome", genomeChosen);

    const continueButton = screen.getByRole("button", { name: /continue/i });
    await waitFor(() => expect(continueButton).toBeEnabled());
    await user.click(continueButton);

    expect(
      screen.getByRole("heading", { name: /name your list/i })
    ).toBeInTheDocument();
    expect(history.at(-1)).toBe("/lists/new/details");
  });

  it("Back on the genome step returns to the taxon URL with the taxon kept", async () => {
    const user = userEvent.setup();
    const { history } = renderWizard("/lists/new/genome", taxonChosen);

    await user.click(screen.getByRole("button", { name: /back/i }));

    expect(history.at(-1)).toBe("/lists/new");
    expect(
      await screen.findByRole("radio", { name: /pinus sylvestris/i })
    ).toBeChecked();
  });

  it("keeps a typed name when going back and forward between steps", async () => {
    const user = userEvent.setup();
    renderWizard("/lists/new/details", genomeChosen);

    await user.type(screen.getByLabelText(/list name/i), "My list");
    await user.click(screen.getByRole("button", { name: /back/i }));

    const continueButton = screen.getByRole("button", { name: /continue/i });
    await waitFor(() => expect(continueButton).toBeEnabled());
    await user.click(continueButton);

    expect(screen.getByLabelText(/list name/i)).toHaveValue("My list");
  });

  it("shows the chosen taxon and genome on the details step", async () => {
    renderWizard("/lists/new/details", genomeChosen);

    expect(
      await screen.findByText(
        /new gene list.*pinus sylvestris.*v2\.0.*araport11/i
      )
    ).toBeInTheDocument();
  });

  it("disables Create list until the list has a name", async () => {
    const user = userEvent.setup();
    renderWizard("/lists/new/details", genomeChosen);

    expect(screen.getByRole("button", { name: /create list/i })).toBeDisabled();
    await user.type(screen.getByLabelText(/list name/i), "My list");
    expect(screen.getByRole("button", { name: /create list/i })).toBeEnabled();
  });

  it("creates the list, goes to it, and resets the wizard", async () => {
    const user = userEvent.setup();
    const { history, store } = renderWizard("/lists/new/details", {
      ...genomeChosen,
      name: "My list",
      description: "old description",
    });

    await user.click(screen.getByRole("button", { name: /create list/i }));

    await waitFor(() => expect(history.at(-1)).toBe("/lists/fake-list-123"));
    expect(store.getState().wizard).toEqual(emptyWizard);
  });

  it("resets the wizard when the user leaves it", async () => {
    const user = userEvent.setup();
    const { history, store } = renderWizard("/lists/new/details", {
      ...genomeChosen,
      name: "My list",
    });

    await user.click(screen.getByRole("link", { name: "Blast" }));

    expect(history.at(-1)).toBe("/blast");
    await waitFor(() => expect(store.getState().wizard).toEqual(emptyWizard));
  });

  it("does not reset the wizard when moving between steps", async () => {
    const user = userEvent.setup();
    const { store } = renderWizard("/lists/new/genome", genomeChosen);

    await user.click(screen.getByRole("button", { name: /back/i }));

    expect(store.getState().wizard).toEqual(genomeChosen);
  });

  it("sends the genome step back to the taxon step without a taxon", async () => {
    const { history } = renderWizard("/lists/new/genome");

    await waitFor(() => expect(history.at(-1)).toBe("/lists/new"));
    expect(
      screen.getByRole("heading", { name: /select a taxon/i })
    ).toBeInTheDocument();
  });

  it("sends the details step back to the taxon step without a taxon", async () => {
    const { history } = renderWizard("/lists/new/details");

    await waitFor(() => expect(history.at(-1)).toBe("/lists/new"));
    expect(screen.queryByRole("button", { name: /create list/i })).toBeNull();
  });

  it("sends the details step back to the genome step without a genome", async () => {
    const { history } = renderWizard("/lists/new/details", taxonChosen);

    await waitFor(() => expect(history.at(-1)).toBe("/lists/new/genome"));
    expect(screen.queryByRole("button", { name: /create list/i })).toBeNull();
  });

  it("sends an unknown path under the wizard to the taxon step", async () => {
    const { history } = renderWizard("/lists/new/whatever", genomeChosen);

    await waitFor(() => expect(history.at(-1)).toBe("/lists/new"));
    expect(
      screen.getByRole("heading", { name: /select a taxon/i })
    ).toBeInTheDocument();
  });

  it("leaves no redirected step in the browser history", async () => {
    const { history } = renderWizard("/lists/new/details");

    await screen.findByRole("heading", { name: /select a taxon/i });

    expect(history).toEqual(["/lists/new"]);
  });
});
