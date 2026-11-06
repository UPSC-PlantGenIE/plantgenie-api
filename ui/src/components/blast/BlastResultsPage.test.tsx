import { describe, it, expect } from "vitest";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { Route, Router } from "wouter";
import { memoryLocation } from "wouter/memory-location";
import { server } from "../../mocks/server";
import { renderWithStore } from "../../test-utils";
import BlastResultsPage from "./BlastResultsPage";

const JOB_ID = "11111111-1111-1111-1111-111111111111";

const HIT = {
  queryId: "PA_chr01_G000001.mRNA.1",
  subjectId: "PA_chr01_G000001.mRNA.1",
  percentIdentity: 100.0,
  alignmentLength: 630,
  mismatches: 0,
  gapOpens: 0,
  queryStart: 1,
  queryEnd: 630,
  subjectStart: 1,
  subjectEnd: 630,
  evalue: 0.0,
  bitScore: 1164.0,
};

const renderResults = () => {
  const { hook } = memoryLocation({ path: `/blast/${JOB_ID}` });
  return renderWithStore(
    <Router hook={hook}>
      <Route path="/blast/:jobId" component={BlastResultsPage} />
    </Router>
  );
};

const mockJob = (status: string, results: unknown[] = []) =>
  server.use(
    http.get("http://localhost:8000/api/v2/blast/poll/:jobId", () =>
      HttpResponse.json({ status })
    ),
    http.get("http://localhost:8000/api/v2/blast/:jobId/json", () =>
      HttpResponse.json({ results })
    )
  );

describe("BlastResultsPage", () => {
  it("renders a row for each hit", async () => {
    mockJob("SUCCESS", [HIT]);
    renderResults();

    const cells = await screen.findAllByRole("cell", {
      name: "PA_chr01_G000001.mRNA.1",
    });
    const row = cells[0].closest("tr");
    expect(row).not.toBeNull();

    const scoped = within(row as HTMLElement);
    expect(scoped.getByRole("cell", { name: "100.000" })).toBeInTheDocument();
    expect(scoped.getByRole("cell", { name: "630" })).toBeInTheDocument();
  });

  it("reports that the search is still running", async () => {
    mockJob("PENDING");
    renderResults();

    expect(await screen.findByText(/running/i)).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("says so when the search found nothing", async () => {
    mockJob("SUCCESS", []);
    renderResults();

    expect(await screen.findByText(/no hits/i)).toBeInTheDocument();
  });

  it("reports a failed search", async () => {
    mockJob("FAILURE");
    renderResults();

    expect(await screen.findByRole("alert")).toHaveTextContent(/failed/i);
  });

  it("offers a TSV export once there are hits", async () => {
    mockJob("SUCCESS", [HIT]);
    renderResults();

    expect(
      await screen.findByRole("link", { name: /export tsv/i })
    ).toHaveAttribute(
      "href",
      `http://localhost:8000/api/v2/blast/${JOB_ID}/tsv`
    );
  });

  it("shows the alignment when a row is clicked and hides it again", async () => {
    const user = userEvent.setup();
    mockJob("SUCCESS", [
      {
        ...HIT,
        queryEnd: 20,
        subjectStart: 101,
        subjectEnd: 121,
        querySequence: "ATGGCTTCAAGT-GCAGTTCC",
        subjectSequence: "ATGGCTACAAGTAGCAGATCC",
      },
    ]);
    renderResults();

    const cells = await screen.findAllByRole("cell", {
      name: "PA_chr01_G000001.mRNA.1",
    });
    await user.click(cells[0]);

    const alignment = screen.getByRole("figure", { name: /alignment/i });
    expect(
      within(alignment).getByText("ATGGCTTCAAGT-GCAGTTCC")
    ).toBeInTheDocument();
    expect(
      within(alignment).getByText("|||||| ||||| |||| |||")
    ).toBeInTheDocument();
    expect(within(alignment).getByText("121")).toBeInTheDocument();

    await user.click(cells[0]);
    expect(screen.queryByRole("figure")).toBeNull();
  });

  it("numbers each alignment block, counting down on the minus strand", async () => {
    const user = userEvent.setup();
    mockJob("SUCCESS", [
      {
        ...HIT,
        queryEnd: 70,
        subjectStart: 200,
        subjectEnd: 131,
        querySequence: "A".repeat(70),
        subjectSequence: "A".repeat(70),
      },
    ]);
    renderResults();

    const cells = await screen.findAllByRole("cell", {
      name: "PA_chr01_G000001.mRNA.1",
    });
    await user.click(cells[0]);

    const alignment = screen.getByRole("figure", { name: /alignment/i });
    expect(within(alignment).getByText("60")).toBeInTheDocument();
    expect(within(alignment).getByText("141")).toBeInTheDocument();
    expect(within(alignment).getByText("61")).toBeInTheDocument();
    expect(within(alignment).getByText("140")).toBeInTheDocument();
    expect(within(alignment).getByText("131")).toBeInTheDocument();
  });

  it("links an opened hit to its gene page", async () => {
    const user = userEvent.setup();
    mockJob("SUCCESS", [
      {
        ...HIT,
        querySequence: "ATGG",
        subjectSequence: "ATGG",
        annotationId: "picab-v2.0",
        geneId: "PA_chr01_G000001",
      },
    ]);
    renderResults();

    const cells = await screen.findAllByRole("cell", {
      name: "PA_chr01_G000001.mRNA.1",
    });
    await user.click(cells[0]);

    expect(screen.getByRole("link", { name: /go to gene/i })).toHaveAttribute(
      "href",
      "/genes/picab-v2.0/PA_chr01_G000001"
    );
  });

  it("stops polling once the search has finished", async () => {
    let pollCount = 0;
    server.use(
      http.get("http://localhost:8000/api/v2/blast/poll/:jobId", () => {
        pollCount += 1;
        return HttpResponse.json({ status: "SUCCESS" });
      }),
      http.get("http://localhost:8000/api/v2/blast/:jobId/json", () =>
        HttpResponse.json({ results: [HIT] })
      )
    );
    renderResults();

    await screen.findAllByRole("cell", { name: "PA_chr01_G000001.mRNA.1" });
    await new Promise((resolve) => setTimeout(resolve, 1500));

    expect(pollCount).toBe(1);
  });

  it("does not offer an export when there are no hits", async () => {
    mockJob("SUCCESS", []);
    renderResults();

    await screen.findByText(/no hits were found/i);
    expect(screen.queryByRole("link", { name: /export tsv/i })).toBeNull();
  });
});
