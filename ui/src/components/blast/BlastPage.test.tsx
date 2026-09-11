import { describe, it, expect } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { server } from "../../mocks/server";
import { renderWithStore } from "../../test-utils";
import BlastPage from "./BlastPage";

const NUCLEOTIDE_QUERY = ">my sequence{enter}ACGTACGTACGT";

async function fillInSearch(databaseId = "picab-v2.0-cds") {
  await screen.findByRole("option", { name: "picab-v2.0-cds" });
  await userEvent.type(screen.getByLabelText(/query/i), NUCLEOTIDE_QUERY);
  await userEvent.selectOptions(
    screen.getByLabelText(/choose database/i),
    databaseId
  );
}

describe("BlastPage", () => {
  it("renders a BLAST heading", () => {
    renderWithStore(<BlastPage />);
    expect(
      screen.getByRole("heading", { name: /blast/i })
    ).toBeInTheDocument();
  });

  it("offers a database dropdown", () => {
    renderWithStore(<BlastPage />);
    expect(screen.getByLabelText(/choose database/i)).toBeEnabled();
  });

  it("disables the program dropdown until a database is chosen", () => {
    renderWithStore(<BlastPage />);
    expect(screen.getByLabelText(/choose program/i)).toBeDisabled();
  });

  it("starts with an empty query and a disabled search button", () => {
    renderWithStore(<BlastPage />);
    expect(screen.getByLabelText(/query/i)).toHaveValue("");
    expect(screen.getByRole("button", { name: /search/i })).toBeDisabled();
  });

  it("lists the available databases by id", async () => {
    renderWithStore(<BlastPage />);
    await screen.findByRole("option", { name: "picab-v2.0-cds" });

    expect(
      within(screen.getByLabelText(/choose database/i))
        .getAllByRole("option")
        .map((option) => option.textContent)
    ).toEqual(["Select a database", "picab-v2.0-cds", "picab-v2.0-protein"]);
  });

  it("complains when the query is not FASTA formatted", async () => {
    renderWithStore(<BlastPage />);
    await userEvent.type(screen.getByLabelText(/query/i), "ATGGAAGATTCA");
    expect(screen.getByRole("alert")).toHaveTextContent(/fasta/i);
  });

  it("keeps the program dropdown disabled until a database is chosen", async () => {
    renderWithStore(<BlastPage />);
    await userEvent.type(
      screen.getByLabelText(/query/i),
      ">my sequence{enter}ACGTACGTACGT"
    );
    expect(screen.getByLabelText(/choose program/i)).toBeDisabled();
  });

  it("keeps the program dropdown disabled until a query is pasted", async () => {
    renderWithStore(<BlastPage />);
    await screen.findByRole("option", { name: "picab-v2.0-cds" });
    await userEvent.selectOptions(
      screen.getByLabelText(/choose database/i),
      "picab-v2.0-cds"
    );
    expect(screen.getByLabelText(/choose program/i)).toBeDisabled();
  });

  it("keeps the program dropdown disabled while the query is not FASTA", async () => {
    renderWithStore(<BlastPage />);
    await screen.findByRole("option", { name: "picab-v2.0-cds" });
    await userEvent.type(
      screen.getByLabelText(/query/i),
      "ACGTACGTACGT"
    );
    await userEvent.selectOptions(
      screen.getByLabelText(/choose database/i),
      "picab-v2.0-cds"
    );
    expect(screen.getByLabelText(/choose program/i)).toBeDisabled();
  });

  it("offers blastn and tblastx for a nucleotide query against nucleotides", async () => {
    renderWithStore(<BlastPage />);
    await screen.findByRole("option", { name: "picab-v2.0-cds" });
    await userEvent.type(
      screen.getByLabelText(/query/i),
      ">my sequence{enter}ACGTACGTACGT"
    );
    await userEvent.selectOptions(
      screen.getByLabelText(/choose database/i),
      "picab-v2.0-cds"
    );

    const programs = screen.getByLabelText(/choose program/i);
    expect(programs).toBeEnabled();
    expect(
      within(programs)
        .getAllByRole("option")
        .map((option) => option.textContent)
    ).toEqual(["blastn", "tblastx"]);
  });

  it("offers blastx for a nucleotide query against proteins", async () => {
    renderWithStore(<BlastPage />);
    await screen.findByRole("option", { name: "picab-v2.0-protein" });
    await userEvent.type(
      screen.getByLabelText(/query/i),
      ">my sequence{enter}ACGTACGTACGT"
    );
    await userEvent.selectOptions(
      screen.getByLabelText(/choose database/i),
      "picab-v2.0-protein"
    );

    expect(
      within(screen.getByLabelText(/choose program/i))
        .getAllByRole("option")
        .map((option) => option.textContent)
    ).toEqual(["blastx"]);
  });

  it("offers tblastn for a protein query against nucleotides", async () => {
    renderWithStore(<BlastPage />);
    await screen.findByRole("option", { name: "picab-v2.0-cds" });
    await userEvent.type(
      screen.getByLabelText(/query/i),
      ">my protein{enter}MEDSQIGLVKRIVHDG"
    );
    await userEvent.selectOptions(
      screen.getByLabelText(/choose database/i),
      "picab-v2.0-cds"
    );

    expect(
      within(screen.getByLabelText(/choose program/i))
        .getAllByRole("option")
        .map((option) => option.textContent)
    ).toEqual(["tblastn"]);
  });

  it("enables search once query, database and program are all chosen", async () => {
    renderWithStore(<BlastPage />);
    await screen.findByRole("option", { name: "picab-v2.0-cds" });
    await userEvent.type(
      screen.getByLabelText(/query/i),
      ">my sequence{enter}ACGTACGTACGT"
    );
    await userEvent.selectOptions(
      screen.getByLabelText(/choose database/i),
      "picab-v2.0-cds"
    );
    await userEvent.selectOptions(
      screen.getByLabelText(/choose program/i),
      "blastn"
    );

    expect(screen.getByRole("button", { name: /search/i })).toBeEnabled();
  });

  it("preselects the program when only one is possible", async () => {
    renderWithStore(<BlastPage />);
    await screen.findByRole("option", { name: "picab-v2.0-protein" });
    await userEvent.type(
      screen.getByLabelText(/query/i),
      ">my sequence{enter}ACGTACGTACGT"
    );
    await userEvent.selectOptions(
      screen.getByLabelText(/choose database/i),
      "picab-v2.0-protein"
    );

    expect(screen.getByLabelText(/choose program/i)).toHaveValue("blastx");
    expect(screen.getByRole("button", { name: /search/i })).toBeEnabled();
  });

  it("disables search again when the query stops being valid", async () => {
    renderWithStore(<BlastPage />);
    await screen.findByRole("option", { name: "picab-v2.0-cds" });
    const queryBox = screen.getByLabelText(/query/i);
    await userEvent.type(queryBox, ">my sequence{enter}ACGTACGTACGT");
    await userEvent.selectOptions(
      screen.getByLabelText(/choose database/i),
      "picab-v2.0-cds"
    );
    await userEvent.clear(queryBox);
    await userEvent.type(queryBox, "ACGTACGTACGT");

    expect(screen.getByRole("button", { name: /search/i })).toBeDisabled();
  });

  it("submits the query, database and program on search", async () => {
    let submitted: unknown = null;
    server.use(
      http.post("http://localhost:8000/api/v2/blast", async ({ request }) => {
        submitted = await request.json();
        return HttpResponse.json({
          jobId: "11111111-1111-1111-1111-111111111111",
        });
      })
    );

    renderWithStore(<BlastPage />);
    await fillInSearch();
    await userEvent.click(screen.getByRole("button", { name: /search/i }));

    await waitFor(() =>
      expect(submitted).toEqual({
        databaseId: "picab-v2.0-cds",
        program: "blastn",
        query: ">my sequence\nACGTACGTACGT",
      })
    );
  });

  it("accepts a query that has a FASTA header", async () => {
    renderWithStore(<BlastPage />);
    await userEvent.type(
      screen.getByLabelText(/query/i),
      ">my sequence{enter}ATGGAAGATTCA"
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
