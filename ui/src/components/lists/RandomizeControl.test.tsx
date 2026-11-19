import { describe, it, expect } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { server } from "../../mocks/server";
import { renderWithStore } from "../../test-utils";
import RandomizeControl from "./RandomizeControl";

const URL = "http://localhost:8000/api/v2/lists/abc-123/random-genes";

const renderControl = () =>
  renderWithStore(<RandomizeControl listId="abc-123" className="btn" />);

describe("RandomizeControl", () => {
  it("explains itself on hover and hides the number box at first", () => {
    renderControl();
    expect(screen.getByRole("button", { name: /randomize/i })).toHaveAttribute(
      "title",
      "Generate a list with random gene IDs"
    );
    expect(screen.queryByLabelText(/number of genes/i)).not.toBeInTheDocument();
  });

  it("opens the number box next to the button; OK stays disabled until the number is valid", async () => {
    const user = userEvent.setup();
    renderControl();
    await user.click(screen.getByRole("button", { name: /randomize/i }));
    const ok = screen.getByRole("button", { name: "OK" });
    expect(ok).toBeDisabled();
    await user.type(screen.getByLabelText(/number of genes/i), "0");
    expect(ok).toBeDisabled();
    await user.clear(screen.getByLabelText(/number of genes/i));
    await user.type(screen.getByLabelText(/number of genes/i), "101");
    expect(ok).toBeDisabled();
    await user.clear(screen.getByLabelText(/number of genes/i));
    await user.type(screen.getByLabelText(/number of genes/i), "25");
    expect(ok).toBeEnabled();
  });

  it("tells the user to choose a number from 1 to 100 while the input is invalid", async () => {
    const user = userEvent.setup();
    renderControl();
    await user.click(screen.getByRole("button", { name: /randomize/i }));
    const input = screen.getByLabelText(/number of genes/i);
    const message = "Please choose a number between 1 and 100.";
    expect(screen.queryByText(message)).not.toBeInTheDocument();
    await user.type(input, "150");
    expect(screen.getByText(message)).toBeInTheDocument();
    await user.clear(input);
    await user.type(input, "25");
    expect(screen.queryByText(message)).not.toBeInTheDocument();
    await user.clear(input);
    await user.type(input, "2a");
    expect(screen.getByText(message)).toBeInTheDocument();
  });

  it("asks the API for that many genes", async () => {
    const user = userEvent.setup();
    let body: unknown;
    server.use(
      http.post(URL, async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ added: 25 });
      })
    );
    renderControl();
    await user.click(screen.getByRole("button", { name: /randomize/i }));
    await user.type(screen.getByLabelText(/number of genes/i), "25");
    await user.click(screen.getByRole("button", { name: "OK" }));
    await waitFor(() => expect(body).toEqual({ count: 25 }));
  });

  it("shows an error when the request fails", async () => {
    const user = userEvent.setup();
    server.use(http.post(URL, () => new HttpResponse(null, { status: 500 })));
    renderControl();
    await user.click(screen.getByRole("button", { name: /randomize/i }));
    await user.type(screen.getByLabelText(/number of genes/i), "5");
    await user.click(screen.getByRole("button", { name: "OK" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      /could not generate genes/i
    );
  });
});
