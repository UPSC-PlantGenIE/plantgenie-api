import { useState } from "react";
import { useGetBlastDatabasesQuery } from "../../api/plantgenieApi";

const PROGRAMS: Record<string, string[]> = {
  "nucl-nucl": ["blastn", "tblastx"],
  "nucl-prot": ["blastx"],
  "prot-nucl": ["tblastn"],
  "prot-prot": ["blastp"],
};

function moleculeTypeOf(query: string) {
  const residues = query
    .split("\n")
    .filter((line) => !line.startsWith(">"))
    .join("")
    .replace(/\s/g, "")
    .toUpperCase();
  return /^[ACGTUN]+$/.test(residues) ? "nucl" : "prot";
}

export default function BlastPage() {
  const { data: databases } = useGetBlastDatabasesQuery();
  const [query, setQuery] = useState("");
  const [databaseId, setDatabaseId] = useState("");
  const [program, setProgram] = useState("");

  const trimmedQuery = query.trim();
  const queryIsInvalid =
    trimmedQuery.length > 0 && !trimmedQuery.startsWith(">");
  const queryIsValid = trimmedQuery.startsWith(">");

  const database = databases?.find((entry) => entry.id === databaseId);
  const programs =
    queryIsValid && database
      ? PROGRAMS[`${moleculeTypeOf(query)}-${database.moleculeType}`]
      : [];
  const selectedProgram = programs.includes(program)
    ? program
    : (programs[0] ?? "");
  const canSearch = queryIsValid && database !== undefined && selectedProgram;

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-8">
      <h1 className="text-2xl font-bold text-heading">BLAST</h1>
      <p className="mt-1 text-sm text-muted">
        Search a sequence against the genomes and annotations hosted here.
      </p>

      <div className="mt-6 flex flex-col gap-5 rounded-xl border border-border bg-card px-6 py-5 shadow-card">
        <div>
          <label
            htmlFor="blast-database"
            className="block text-xs font-medium text-label"
          >
            Choose database
          </label>
          <select
            id="blast-database"
            value={databaseId}
            onChange={(event) => {
              setDatabaseId(event.target.value);
              setProgram("");
            }}
            className="mt-1 h-11 w-full rounded-lg border border-border bg-card px-3 text-sm text-heading"
          >
            <option value="">Select a database</option>
            {databases?.map((database) => (
              <option key={database.id} value={database.id}>
                {database.taxonScientificName} — {database.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label
            htmlFor="blast-program"
            className="block text-xs font-medium text-label"
          >
            Choose program
          </label>
          <select
            id="blast-program"
            value={selectedProgram}
            onChange={(event) => setProgram(event.target.value)}
            disabled={programs.length === 0}
            className="mt-1 h-11 w-full rounded-lg border border-border bg-card px-3 text-sm text-heading disabled:opacity-50"
          >
            {programs.length === 0 ? (
              <option value="">Select a program</option>
            ) : (
              programs.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))
            )}
          </select>
        </div>

        <div>
          <label
            htmlFor="blast-query"
            className="block text-xs font-medium text-label"
          >
            Query
          </label>
          <textarea
            id="blast-query"
            rows={10}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Paste one or more FASTA-formatted sequences"
            className="mt-1 w-full rounded-lg border border-border bg-card px-3 py-2 font-mono text-xs text-heading"
          />
          {queryIsInvalid && (
            <p role="alert" className="mt-2 text-xs text-red-600">
              Your query must be in FASTA format, beginning with a header
              line such as &gt;my sequence
            </p>
          )}
        </div>

        <button
          type="button"
          disabled={!canSearch}
          className="h-11 cursor-pointer rounded-lg bg-primary px-5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          Search
        </button>
      </div>
    </div>
  );
}
