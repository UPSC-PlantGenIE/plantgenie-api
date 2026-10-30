import { useParams } from "wouter";
import {
  baseUrl,
  useGetBlastResultsQuery,
  usePollBlastQuery,
} from "../../api/plantgenieApi";

const COLUMNS = [
  ["queryId", "Query"],
  ["subjectId", "Subject"],
  ["percentIdentity", "Identity"],
  ["alignmentLength", "Length"],
  ["mismatches", "Mismatches"],
  ["gapOpens", "Gaps"],
  ["evalue", "E-value"],
  ["bitScore", "Bit score"],
] as const;

export default function BlastResultsPage() {
  const { jobId } = useParams<{ jobId: string }>();

  const { data: job } = usePollBlastQuery(jobId, {
    pollingInterval: 1000,
    skipPollingIfUnfocused: true,
  });
  const isFinished = job?.status === "SUCCESS" || job?.status === "FAILURE";

  const { data: hits } = useGetBlastResultsQuery(jobId, {
    skip: job?.status !== "SUCCESS",
  });

  return (
    <div className="mx-auto w-full max-w-7xl px-6 py-8">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-heading">BLAST results</h1>
        {hits !== undefined && hits.length > 0 && (
          <a
            href={`${baseUrl}v2/blast/${jobId}/tsv`}
            className="inline-flex h-11 items-center rounded-lg bg-primary px-5 text-sm font-semibold text-white transition hover:brightness-95 active:brightness-90"
          >
            Export TSV
          </a>
        )}
      </div>

      {!isFinished && (
        <p className="mt-4 text-sm text-muted">Running your search…</p>
      )}

      {job?.status === "FAILURE" && (
        <p role="alert" className="mt-4 text-sm text-red-600">
          Your search failed. Try again, or check the query and database.
        </p>
      )}

      {hits?.length === 0 && (
        <p className="mt-4 text-sm text-muted">
          No hits were found for your query.
        </p>
      )}

      {hits !== undefined && hits.length > 0 && (
        <div className="mt-6 overflow-x-auto rounded-xl border border-border bg-card shadow-card">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border">
                {COLUMNS.map(([field, heading]) => (
                  <th
                    key={field}
                    className="px-4 py-3 font-medium text-label"
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {hits.map((hit, index) => (
                <tr
                  key={`${hit.queryId}-${hit.subjectId}-${index}`}
                  className="border-b border-border last:border-0"
                >
                  {COLUMNS.map(([field]) => (
                    <td key={field} className="px-4 py-3 text-heading">
                      {field === "percentIdentity"
                        ? hit[field].toFixed(3)
                        : hit[field]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
