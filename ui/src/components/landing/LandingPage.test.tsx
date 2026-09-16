import { describe, it, expect, beforeEach } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { Route, Router } from "wouter";
import { memoryLocation } from "wouter/memory-location";
import { server } from "../../mocks/server";
import type { RootState } from "../../store";
import { renderWithStore } from "../../test-utils";
import LandingPage from "./LandingPage";

const ACCOUNT_ID = "1234567890123456";
const STORED_ACCOUNT_ID = "0000111122223333";
const GENERATED_ACCOUNT_ID = "9876543210987654";

const mockCreateAccount = () => {
  server.use(
    http.post("http://localhost:8000/api/v2/accounts", () =>
      HttpResponse.json({ accountId: GENERATED_ACCOUNT_ID }, { status: 201 })
    )
  );
};

const renderLanding = (preloadedState?: Partial<RootState>) => {
  const { hook, history } = memoryLocation({ path: "/", record: true });

  const utils = renderWithStore(
    <Router hook={hook}>
      <Route path="/" component={LandingPage} />
    </Router>,
    { preloadedState }
  );

  return { ...utils, history };
};

describe("LandingPage", () => {
  beforeEach(() => localStorage.clear());

  it("redirects if a valid user is logged in already", async () => {
    const { history } = renderLanding({
      account: { accountId: STORED_ACCOUNT_ID },
    });
    await waitFor(() => expect(history).toContain("/lists"), { timeout: 3 });
  });

  it("shows the returning user and new-user cards to new user or returning user", () => {
    renderLanding();

    expect(
      screen.getByRole("region", { name: /first time here/i })
    ).toBeInTheDocument();

    expect(
      screen.queryByRole("region", { name: "Returning User?" })
    ).toBeInTheDocument();
  });

  it("puts the login form in the existing-account card", () => {
    renderLanding();

    const card = screen.getByRole("region", { name: "Returning User?" });
    expect(within(card).getByText(/no email/i)).toBeInTheDocument();
    expect(within(card).getByLabelText(/account id/i)).toHaveAttribute(
      "placeholder",
      "1234 5678 9012 3456"
    );
    expect(
      within(card).getByRole("button", { name: /continue/i })
    ).toBeInTheDocument();
  });

  it("offers to generate a new id in the new-account card", () => {
    renderLanding();

    const card = screen.getByRole("region", { name: /first time here/i });
    expect(
      within(card).getByRole("button", { name: /generate a new id/i })
    ).toBeInTheDocument();
  });

  it("shows a generated id in groups of four with a warning", async () => {
    mockCreateAccount();
    const { store } = renderLanding();

    await userEvent.click(
      screen.getByRole("button", { name: /generate a new id/i })
    );

    expect(await screen.findByText("9876 5432 1098 7654")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(/lose/i);
    expect(store.getState().account.accountId).toBeNull();
  });

  it("copies a generated id to the clipboard", async () => {
    mockCreateAccount();
    const user = userEvent.setup();
    renderLanding();

    await user.click(
      screen.getByRole("button", { name: /generate a new id/i })
    );
    await user.click(await screen.findByRole("button", { name: /copy id/i }));

    expect(await navigator.clipboard.readText()).toBe(GENERATED_ACCOUNT_ID);
    expect(screen.getByRole("button", { name: /copied/i })).toBeInTheDocument();
  });

  it("continues to my lists after generating an id", async () => {
    mockCreateAccount();
    const { store, history } = renderLanding();

    await userEvent.click(
      screen.getByRole("button", { name: /generate a new id/i })
    );
    await userEvent.click(
      await screen.findByRole("link", { name: /continue to my lists/i })
    );

    expect(history).toContain("/lists");
    expect(store.getState().account.accountId).toBe(GENERATED_ACCOUNT_ID);
  });

  // it("welcomes back a signed-in visitor", () => {
  //   renderLanding({ account: { accountId: STORED_ACCOUNT_ID } });

  //   const card = screen.getByRole("region", { name: /welcome back/i });
  //   expect(within(card).getByText("0000 1111 2222 3333")).toBeInTheDocument();
  // });

  // it("continues to my lists from the welcome-back card", async () => {
  //   const { history } = renderLanding({
  //     account: { accountId: STORED_ACCOUNT_ID },
  //   });

  //   const card = screen.getByRole("region", { name: /welcome back/i });
  //   await userEvent.click(
  //     within(card).getByRole("link", { name: /continue to my lists/i })
  //   );

  //   expect(history).toContain("/lists");
  // });

  it("accepts an id typed in groups of four", async () => {
    const { store } = renderLanding();

    await userEvent.type(
      screen.getByRole("textbox", { name: /account id/i }),
      "1234 5678 9012 3456"
    );
    await userEvent.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() =>
      expect(store.getState().account.accountId).toBe(ACCOUNT_ID)
    );
  });

  it("signs in with a pasted account id", async () => {
    const { history, store } = renderLanding();

    await userEvent.type(
      screen.getByRole("textbox", { name: /account id/i }),
      ACCOUNT_ID
    );
    await userEvent.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => expect(history).toContain("/lists"));
    expect(store.getState().account.accountId).toBe(ACCOUNT_ID);
  });

  // it("verifies the pasted id, not the stored one", async () => {
  //   let authorization: string | null = null;
  //   server.use(
  //     http.get("http://localhost:8000/api/v2/accounts/me", ({ request }) => {
  //       authorization = request.headers.get("Authorization");
  //       return HttpResponse.json(null);
  //     })
  //   );
  //   renderLanding({ account: { accountId: STORED_ACCOUNT_ID } });

  //   await userEvent.type(
  //     screen.getByRole("textbox", { name: /account id/i }),
  //     ACCOUNT_ID
  //   );
  //   await userEvent.click(screen.getByRole("button", { name: /continue/i }));

  //   await waitFor(() => expect(authorization).toBe(`Bearer ${ACCOUNT_ID}`));
  // });

  it("shows an alert when the pasted id is rejected", async () => {
    server.use(
      http.get("http://localhost:8000/api/v2/accounts/me", () =>
        HttpResponse.json({ detail: "Unknown account" }, { status: 401 })
      )
    );
    const { history, store } = renderLanding();

    await userEvent.type(
      screen.getByRole("textbox", { name: /account id/i }),
      ACCOUNT_ID
    );
    await userEvent.click(screen.getByRole("button", { name: /continue/i }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(history).not.toContain("/lists");
    expect(store.getState().account.accountId).toBeNull();
  });
});
