import { describe, it, expect, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { Router } from "wouter";
import { memoryLocation } from "wouter/memory-location";
import App from "../../App";
import { server } from "../../mocks/server";
import type { RootState } from "../../store";
import { renderWithStore } from "../../test-utils";

const STORED_ACCOUNT_ID = "0000111122223333";
const GENERATED_ACCOUNT_ID = "9876543210987654";

const mockCreateAccount = () => {
  server.use(
    http.post("http://localhost:8000/api/v2/accounts", () =>
      HttpResponse.json({ accountId: GENERATED_ACCOUNT_ID }, { status: 201 })
    )
  );
};

const renderNewAccount = (preloadedState?: Partial<RootState>) => {
  const { hook, history } = memoryLocation({
    path: "/accounts/new",
    record: true,
  });

  const utils = renderWithStore(
    <Router hook={hook}>
      <App />
    </Router>,
    { preloadedState }
  );

  return { ...utils, history };
};

describe("NewAccountPage", () => {
  beforeEach(() => localStorage.clear());

  it("offers to generate a new id", () => {
    renderNewAccount();

    expect(
      screen.getByRole("button", { name: /generate a new id/i })
    ).toBeInTheDocument();
  });

  it("links back to sign in", () => {
    renderNewAccount();

    expect(screen.getByRole("link", { name: /sign in/i })).toHaveAttribute(
      "href",
      "/"
    );
  });

  it("redirects a signed-in visitor to my lists", async () => {
    const { history } = renderNewAccount({
      account: { accountId: STORED_ACCOUNT_ID },
    });

    await waitFor(() => expect(history.at(-1)).toBe("/lists"));
  });

  it("shows a generated id in groups of four with a warning", async () => {
    mockCreateAccount();
    const { store } = renderNewAccount();

    await userEvent.click(
      screen.getByRole("button", { name: /generate a new id/i })
    );

    expect(await screen.findByText("9876 5432 1098 7654")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(/lose/i);
    expect(store.getState().account.accountId).toBeNull();
  });

  it("stops offering sign in once an id is shown", async () => {
    mockCreateAccount();
    renderNewAccount();

    await userEvent.click(
      screen.getByRole("button", { name: /generate a new id/i })
    );

    await screen.findByText("9876 5432 1098 7654");
    expect(screen.queryByRole("link", { name: /sign in/i })).toBeNull();
  });

  it("copies a generated id to the clipboard", async () => {
    mockCreateAccount();
    const user = userEvent.setup();
    renderNewAccount();

    await user.click(
      screen.getByRole("button", { name: /generate a new id/i })
    );
    await user.click(await screen.findByRole("button", { name: /copy id/i }));

    expect(await navigator.clipboard.readText()).toBe(GENERATED_ACCOUNT_ID);
    expect(screen.getByRole("button", { name: /copied/i })).toBeInTheDocument();
  });

  it("shows the error page when the account cannot be created", async () => {
    server.use(
      http.post("http://localhost:8000/api/v2/accounts", () =>
        HttpResponse.json({ detail: "Server error" }, { status: 500 })
      )
    );
    const user = userEvent.setup();
    renderNewAccount();

    await user.click(
      screen.getByRole("button", { name: /generate a new id/i })
    );

    expect(
      await screen.findByRole("heading", { name: /something went wrong/i })
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /try again/i }));

    expect(
      screen.getByRole("button", { name: /generate a new id/i })
    ).toBeInTheDocument();
  });

  it("continues to my lists after generating an id", async () => {
    mockCreateAccount();
    const { store, history } = renderNewAccount();

    await userEvent.click(
      screen.getByRole("button", { name: /generate a new id/i })
    );
    await userEvent.click(
      await screen.findByRole("link", { name: /continue to my lists/i })
    );

    expect(history).toContain("/lists");
    expect(store.getState().account.accountId).toBe(GENERATED_ACCOUNT_ID);
  });
});
