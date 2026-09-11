import { describe, it, expect } from "vitest";
import { screen, within } from "@testing-library/react";
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
    http.get(
      "http://localhost:8000/api/v2/blast/poll/:jobId",
      () => HttpResponse.json({ status })
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
});
