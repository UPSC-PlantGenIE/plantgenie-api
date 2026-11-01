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

  it("shows one sign-in panel", () => {
    renderLanding();

    const panel = screen.getByRole("region", { name: /sign in/i });
    expect(within(panel).getByText(/no email/i)).toBeInTheDocument();
    expect(within(panel).getByLabelText(/account id/i)).toHaveAttribute(
      "placeholder",
      "1234 5678 9012 3456"
    );
    expect(
      within(panel).getByRole("button", { name: /continue/i })
    ).toBeInTheDocument();
    expect(screen.getAllByRole("region")).toHaveLength(1);
  });

  it("does not generate ids on the sign-in page", () => {
    renderLanding();

    expect(
      screen.queryByRole("button", { name: /generate a new id/i })
    ).toBeNull();
  });

  it("sends new visitors to the new account page", async () => {
    const { history } = renderLanding();

    await userEvent.click(screen.getByRole("link", { name: /new here/i }));

    expect(history).toContain("/accounts/new");
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

  it("shows the error page when the sign-in check fails", async () => {
    server.use(
      http.get("http://localhost:8000/api/v2/accounts/me", () =>
        HttpResponse.json({ detail: "Server error" }, { status: 500 })
      )
    );
    const user = userEvent.setup();
    renderLanding();

    await user.type(
      screen.getByRole("textbox", { name: /account id/i }),
      ACCOUNT_ID
    );
    await user.click(screen.getByRole("button", { name: /continue/i }));

    expect(
      await screen.findByRole("heading", { name: /something went wrong/i })
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /try again/i }));

    expect(screen.getByRole("textbox", { name: /account id/i })).toHaveValue(
      ACCOUNT_ID
    );
  });

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

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /wasn't recognised/i
    );
    expect(
      screen.queryByRole("heading", { name: /something went wrong/i })
    ).toBeNull();
    expect(history).not.toContain("/lists");
    expect(store.getState().account.accountId).toBeNull();
  });
});
