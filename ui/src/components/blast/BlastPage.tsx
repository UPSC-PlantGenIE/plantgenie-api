import { useState, type CSSProperties } from "react";
import { useLocation } from "wouter";
import {
  useGetBlastDatabasesQuery,
  useSubmitBlastMutation,
} from "../../api/plantgenieApi";

const PROGRAMS: Record<string, string[]> = {
  "nucl-nucl": ["blastn", "tblastx"],
  "nucl-prot": ["blastx"],
  "prot-nucl": ["tblastn"],
  "prot-prot": ["blastp"],
};

const MINIMUM_EVALUE = 1e-30;
const MAXIMUM_EVALUE = 10;
const MINIMUM_HITS = 1;
const MAXIMUM_HITS = 100;

function rangeFill(value: number, minimum: number, maximum: number) {
  const percent = ((value - minimum) / (maximum - minimum)) * 100;
  return { "--range-fill": `${percent}%` } as CSSProperties;
}

function parseTyped(text: string) {
  const value = Number(text.trim());
  return text.trim() === "" || Number.isNaN(value) ? null : value;
}

function clip(value: number, minimum: number, maximum: number) {
  return Math.min(Math.max(value, minimum), maximum);
}

function formatEvalue(value: number) {
  return value >= 0.01 ? String(value) : value.toExponential();
}

type RangeFieldProps = {
  id: string;
  label: string;
  minimum: number;
  maximum: number;
  position: number;
  displayValue: string;
  onSlide: (position: number) => void;
  onType: (text: string) => void;
};

function RangeField({
  id,
  label,
  minimum,
  maximum,
  position,
  displayValue,
  onSlide,
  onType,
}: RangeFieldProps) {
  const [draft, setDraft] = useState<string | null>(null);

  function apply() {
    if (draft !== null) onType(draft);
    setDraft(null);
  }

  return (
    <div>
      <label htmlFor={id} className="block text-xs font-medium text-label">
        {label}
      </label>
      <div className="mt-1 flex items-center gap-3">
        <input
          id={id}
          type="range"
          min={minimum}
          max={maximum}
          value={position}
          onChange={(event) => onSlide(Number(event.target.value))}
          style={rangeFill(position, minimum, maximum)}
          className="range-input w-full"
        />
        <input
          type="text"
          aria-label={label}
          value={draft ?? displayValue}
          onChange={(event) => setDraft(event.target.value)}
          onBlur={apply}
          onKeyDown={(event) => {
            if (event.key === "Enter") apply();
          }}
          className="h-11 w-16 shrink-0 rounded-lg border border-border bg-card text-center text-sm text-heading"
        />
      </div>
    </div>
  );
}

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
  const [submitBlast, { isLoading: isSubmitting }] = useSubmitBlastMutation();
  const [query, setQuery] = useState("");
  const [databaseId, setDatabaseId] = useState("");
  const [program, setProgram] = useState("");
  const [evalue, setEvalue] = useState(1e-4);
  const [maxHits, setMaxHits] = useState(50);
  const [submitError, setSubmitError] = useState("");
  const [, setLocation] = useLocation();

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
                {database.id}
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

        <div className="grid gap-5 sm:grid-cols-2">
          <RangeField
            id="blast-evalue"
            label="E-value"
            minimum={Math.log10(MINIMUM_EVALUE)}
            maximum={Math.log10(MAXIMUM_EVALUE)}
            position={Math.round(Math.log10(evalue))}
            displayValue={formatEvalue(evalue)}
            onSlide={(position) => setEvalue(Number(`1e${position}`))}
            onType={(text) => {
              const value = parseTyped(text);
              if (value !== null) {
                setEvalue(clip(value, MINIMUM_EVALUE, MAXIMUM_EVALUE));
              }
            }}
          />
          <RangeField
            id="blast-max-hits"
            label="Max hits"
            minimum={MINIMUM_HITS}
            maximum={MAXIMUM_HITS}
            position={maxHits}
            displayValue={String(maxHits)}
            onSlide={setMaxHits}
            onType={(text) => {
              const value = parseTyped(text);
              if (value !== null) {
                setMaxHits(clip(Math.round(value), MINIMUM_HITS, MAXIMUM_HITS));
              }
            }}
          />
        </div>

        <button
          type="button"
          disabled={!canSearch || isSubmitting}
          onClick={async () => {
            setSubmitError("");
            try {
              const { jobId } = await submitBlast({
                databaseId,
                program: selectedProgram,
                query,
                parameters: {
                  evalue,
                  maxTargetSeqs: maxHits,
                },
              }).unwrap();
              setLocation(`/blast/${jobId}`);
            } catch (error) {
              const detail = (error as { data?: { detail?: unknown } }).data
                ?.detail;
              const messages = Array.isArray(detail)
                ? detail.map((entry: { msg: string }) => entry.msg).join(" ")
                : detail;
              setSubmitError(
                typeof messages === "string" && messages
                  ? messages
                  : "Your search could not be submitted. Please try again."
              );
            }
          }}
          className="h-11 cursor-pointer rounded-lg bg-primary px-5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isSubmitting ? (
            <span
              role="status"
              aria-label="Submitting search"
              className="inline-block size-5 animate-spin rounded-full border-2 border-white border-t-transparent"
            />
          ) : (
            "Search"
          )}
        </button>
        {submitError && (
          <p role="alert" className="text-xs text-red-600">
            {submitError}
          </p>
        )}
      </div>
    </div>
  );
}
