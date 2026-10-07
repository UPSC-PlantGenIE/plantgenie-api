import { useState } from "react";
import { Link, useLocation, useParams } from "wouter";
import {
  useGetListQuery,
  useLookupGenesQuery,
  usePatchListMutation,
} from "../../api/plantgenieApi";
import { titleTopic } from "./listTitle";
import {
  DEFAULT_NUMBER_OF_RESULTS,
  findSemanticSpecies,
  useGetSemanticSpeciesQuery,
  useSemanticSearchQuery,
} from "../../api/semanticSearchApi";

const RESULT_PRESETS = [10, 25, 50, 100];

export default function SemanticSearchPage() {
  const { listId } = useParams<{ listId: string }>();
  const [, setLocation] = useLocation();
  const { data: list } = useGetListQuery(listId ?? "", { skip: !listId });
  const { data: speciesList, isLoading: speciesLoading } =
    useGetSemanticSpeciesQuery();
  const species = findSemanticSpecies(speciesList, list?.taxonName);
  // "<topic> in <species>" list titles suggest "<topic>" as the example.
  const suggestedQuery = list && titleTopic(list.name, list.taxonName);

  const [text, setText] = useState("");
  const [query, setQuery] = useState("");
  const [numberOfResults, setNumberOfResults] = useState(
    DEFAULT_NUMBER_OF_RESULTS
  );
  const [draft, setDraft] = useState(String(DEFAULT_NUMBER_OF_RESULTS));
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [patchList, { isLoading: isAdding }] = usePatchListMutation();

  const {
    data: hits,
    isFetching,
    isError,
  } = useSemanticSearchQuery(
    {
      species: species?.abbreviation ?? "",
      query,
      numberOfResults,
    },
    { skip: !species || query === "" }
  );

  // Only genes that exist in the list's annotation can be added.
  const { data: lookup } = useLookupGenesQuery(
    {
      annotationId: list?.annotationId ?? "",
      geneIds: hits?.map((h) => h.geneId) ?? [],
    },
    { skip: !list || !hits || hits.length === 0 }
  );

  const inList = new Set(list?.memberGeneIds ?? []);
  const known = new Set(lookup?.found.map((g) => g.geneId) ?? []);
  const isAddable = (geneId: string) =>
    known.has(geneId) && !inList.has(geneId);
  const addable = (hits ?? []).filter((h) => isAddable(h.geneId));
  const selectedCount = selected.size;

  // Typing is kept as a draft and applied on Enter/blur, so each
  // keystroke doesn't trigger a new search.
  const applyNumberOfResults = (value: string) => {
    const parsed = Math.floor(Number(value));
    if (Number.isFinite(parsed) && parsed >= 1) {
      setSelected(new Set());
      setNumberOfResults(parsed);
      setDraft(String(parsed));
    } else {
      setDraft(String(numberOfResults));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSelected(new Set());
    setQuery(text.trim());
  };

  const toggle = (geneId: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(geneId)) next.delete(geneId);
      else next.add(geneId);
      return next;
    });

  const toggleAll = () =>
    setSelected(
      selectedCount === addable.length
        ? new Set()
        : new Set(addable.map((h) => h.geneId))
    );

  const handleAdd = async () => {
    if (!listId || selectedCount === 0) return;
    await patchList({ listId, addGeneIds: Array.from(selected) }).unwrap();
    setLocation(`/lists/${listId}`);
  };

  if (list && !speciesLoading && !species) {
    return (
      <div className="mx-auto w-full max-w-7xl px-6 py-8">
        <p className="text-sm text-muted">
          Semantic search is not applicable yet for {list.taxonName}.
        </p>
        <Link
          href={`/lists/${listId}`}
          className="mt-2 inline-block text-sm font-semibold text-primary"
        >
          ← Back to list
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-7xl px-6 py-8">
      <nav className="text-xs text-muted" aria-label="Breadcrumb">
        <Link href="/lists" className="hover:text-heading">
          My Lists
        </Link>
        <span className="px-2">/</span>
        <Link href={`/lists/${listId}`} className="hover:text-heading">
          {list?.name ?? "List"}
        </Link>
        <span className="px-2">/</span>
        <span>Search genes</span>
      </nav>

      <h1 className="mt-4 text-xl font-bold text-heading">Search genes</h1>
      <p className="mt-1 text-sm text-muted">
        Describe a function or process
        {species ? ` to search ${species.scientificName} genes` : ""}. Select
        genes to add to your list.
      </p>

      <form onSubmit={handleSubmit} className="mt-5 flex gap-2">
        <input
          autoFocus
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={`e.g. ${suggestedQuery ?? "cell wall biosynthesis, drought response…"}`}
          onKeyDown={(e) => {
            if (e.key === "Tab" && !e.shiftKey && !text && suggestedQuery) {
              e.preventDefault();
              setText(suggestedQuery);
            }
          }}
          aria-label="Search query"
          className="h-11 flex-1 rounded-lg border border-border bg-card px-4 text-sm text-heading focus:border-primary focus:outline-none"
        />
        <button
          type="submit"
          disabled={!species || text.trim() === "" || isFetching}
          className="h-11 rounded-lg bg-primary px-6 text-sm font-semibold text-white shadow-card disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isFetching ? "Searching…" : "Search"}
        </button>
      </form>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-muted">
        <label htmlFor="number-of-results">Results to show</label>
        <input
          id="number-of-results"
          type="number"
          min={1}
          step={1}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={(e) => applyNumberOfResults(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") applyNumberOfResults(e.currentTarget.value);
          }}
          className="h-8 w-24 rounded-md border border-border bg-card px-2 text-heading focus:border-primary focus:outline-none"
        />
        {RESULT_PRESETS.map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => applyNumberOfResults(String(n))}
            aria-pressed={numberOfResults === n}
            className={`h-8 rounded-md border px-3 text-xs font-semibold ${
              numberOfResults === n
                ? "border-primary bg-primary-tint text-primary"
                : "border-border bg-card text-label"
            }`}
          >
            {n}
          </button>
        ))}
      </div>

      {isError && (
        <p role="alert" className="mt-3 text-sm text-red-600">
          Something went wrong while searching. Please try again.
        </p>
      )}

      {hits && !isError && (
        <section className="mt-5 overflow-hidden rounded-xl border border-border bg-card shadow-card">
          {hits.length === 0 ? (
            <p className="p-8 text-center text-sm text-muted">
              No genes matched “{query}”.
            </p>
          ) : (
            <>
              <div className="flex items-center justify-between border-b border-border bg-surface px-6 py-3 text-xs font-semibold text-muted">
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={
                      addable.length > 0 && selectedCount === addable.length
                    }
                    disabled={addable.length === 0}
                    onChange={toggleAll}
                  />
                  Select / deselect all
                </label>
                <span>
                  {selectedCount} of {addable.length} selected
                </span>
              </div>
              <ul>
                {hits.map((hit) => {
                  const addableHit = isAddable(hit.geneId);
                  const status = inList.has(hit.geneId)
                    ? "Already in list"
                    : lookup && !known.has(hit.geneId)
                      ? "Not in this annotation"
                      : "";
                  return (
                    <li
                      key={hit.geneId}
                      className="flex items-start gap-3 border-b border-border px-6 py-3 last:border-b-0"
                    >
                      <input
                        type="checkbox"
                        aria-label={`Select ${hit.geneId}`}
                        className="mt-1"
                        checked={selected.has(hit.geneId)}
                        disabled={!addableHit}
                        onChange={() => toggle(hit.geneId)}
                      />
                      <div
                        className={`min-w-0 flex-1 ${addableHit ? "" : "opacity-50"}`}
                      >
                        <span className="text-sm font-semibold text-primary">
                          {hit.geneId}
                        </span>
                        <p className="truncate text-sm text-muted">
                          {hit.description}
                        </p>
                      </div>
                      <span className="shrink-0 text-xs text-muted">
                        {status ||
                          `${(hit.similarity * 100).toFixed(0)}% match`}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </section>
      )}

      <div className="mt-6 flex justify-between">
        <Link
          href={`/lists/${listId}`}
          className="inline-flex h-11 items-center rounded-lg border border-border bg-card px-6 text-sm font-semibold text-label shadow-card"
        >
          ← Back to list
        </Link>
        <button
          type="button"
          onClick={handleAdd}
          disabled={selectedCount === 0 || isAdding}
          className="h-11 rounded-lg bg-primary px-6 text-sm font-semibold text-white shadow-card disabled:cursor-not-allowed disabled:opacity-50"
        >
          Add {selectedCount} gene{selectedCount === 1 ? "" : "s"} to list →
        </button>
      </div>
    </div>
  );
}
