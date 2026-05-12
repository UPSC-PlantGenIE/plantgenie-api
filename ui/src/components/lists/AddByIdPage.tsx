import { useEffect, useRef, useState } from "react";
import { useLocation, useParams } from "wouter";
import {
  useGetListQuery,
  useLazyLookupGenesQuery,
  usePatchListMutation,
} from "../../api/plantgenieApi";

export default function AddByIdPage() {
  const { listId } = useParams<{ listId: string }>();
  const [, setLocation] = useLocation();
  const { data: list } = useGetListQuery(listId ?? "", {
    skip: !listId,
  });
  const [lookup, { data: result }] = useLazyLookupGenesQuery();
  const [patchList] = usePatchListMutation();
  const [text, setText] = useState("");
  const [orderedIds, setOrderedIds] = useState<string[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [view, setView] = useState<"input" | "results">("input");

  useEffect(() => {
    if (result) {
      setSelected(new Set(result.found.map((g) => g.geneId)));
    }
  }, [result]);

  const handleValidate = async () => {
    if (!list) return;
    const geneIds = Array.from(
      new Set(
        text
          .split(/[\s,]+/)
          .map((g) => g.trim())
          .filter(Boolean)
      )
    );
    if (geneIds.length === 0) return;
    setOrderedIds(geneIds);
    await lookup({ annotationId: list.annotationId, geneIds });
    setView("results");
  };

  const handleAdd = async () => {
    if (!listId) return;
    await patchList({
      listId,
      addGeneIds: Array.from(selected),
    }).unwrap();
    setLocation(`/lists/${listId}`);
  };

  const toggle = (geneId: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(geneId)) {
        next.delete(geneId);
      } else {
        next.add(geneId);
      }
      return next;
    });
  };

  const foundCount = result?.found.length ?? 0;
  const notFoundCount = result?.notFound.length ?? 0;
  const allSelected = foundCount > 0 && selected.size === foundCount;
  const noneSelected = selected.size === 0;
  const selectAllRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (selectAllRef.current) {
      selectAllRef.current.indeterminate = !allSelected && !noneSelected;
    }
  }, [allSelected, noneSelected]);

  const toggleAll = () => {
    if (allSelected) {
      setSelected(new Set());
    } else {
      setSelected(new Set(result?.found.map((g) => g.geneId) ?? []));
    }
  };

  if (view === "input" || !result) {
    return (
      <div className="mx-auto w-full max-w-3xl px-6 py-8">
        <textarea
          aria-label="Gene IDs"
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="h-40 w-full rounded-lg border border-border bg-card p-3 text-sm"
        />
        <button
          type="button"
          onClick={handleValidate}
          className="mt-3 inline-flex h-11 items-center justify-center rounded-lg bg-primary px-5 text-sm font-semibold text-white shadow-card"
        >
          Validate
        </button>
      </div>
    );
  }

  const annotationVersion =
    list?.annotationId.split("-").slice(1).join("-") ?? "";

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-8">
      <header>
        <h1 className="text-xl font-bold text-heading">
          Review validation results
        </h1>
        <p className="mt-1 text-sm text-muted">
          {orderedIds.length} {orderedIds.length === 1 ? "ID" : "IDs"} checked
          against {list?.taxonName} {annotationVersion}
        </p>
        <div className="mt-3 flex gap-2">
          <span className="rounded-md bg-green-50 px-2.5 py-1 text-xs font-medium text-green-700">
            {foundCount} valid
          </span>
          <span className="rounded-md bg-red-50 px-2.5 py-1 text-xs font-medium text-red-700">
            {notFoundCount} not found
          </span>
        </div>
      </header>

      {foundCount > 0 && (
        <section
          aria-labelledby="valid-genes-heading"
          className="mt-6 overflow-hidden rounded-xl border border-green-200 bg-card shadow-card"
        >
          <header className="border-b border-green-200 bg-green-50 px-4 py-3">
            <h2
              id="valid-genes-heading"
              className="text-sm font-semibold text-green-700"
            >
              ✓ Valid genes — will be added to your list
            </h2>
          </header>
          <label className="flex cursor-pointer items-center gap-3 border-b border-border px-4 py-3 text-sm font-semibold text-label">
            <input
              ref={selectAllRef}
              type="checkbox"
              checked={allSelected}
              onChange={toggleAll}
              className="size-4"
            />
            Select all
          </label>
          <ul>
            {result.found.map((gene) => (
              <li
                key={gene.geneId}
                className="border-b border-border last:border-b-0"
              >
                <label className="flex cursor-pointer items-start gap-3 px-4 py-3 text-sm">
                  <input
                    type="checkbox"
                    checked={selected.has(gene.geneId)}
                    onChange={() => toggle(gene.geneId)}
                    className="mt-1 size-4"
                  />
                  <div>
                    <div className="font-semibold text-primary">
                      {gene.geneId}
                      {gene.name && <em> – {gene.name}</em>}
                    </div>
                    <div className="text-xs text-muted">
                      {gene.description}
                    </div>
                  </div>
                </label>
              </li>
            ))}
          </ul>
        </section>
      )}

      {notFoundCount > 0 && (
        <section
          aria-labelledby="not-found-heading"
          className="mt-4 overflow-hidden rounded-xl border border-red-200 bg-card shadow-card"
        >
          <header className="border-b border-red-200 bg-red-50 px-4 py-3">
            <h2
              id="not-found-heading"
              className="text-sm font-semibold text-red-700"
            >
              ✗ Not found in {list?.taxonName} {annotationVersion}
            </h2>
          </header>
          <ul>
            {result.notFound.map((id) => (
              <li
                key={id}
                className="border-b border-border px-4 py-3 last:border-b-0"
              >
                <div className="text-sm font-semibold text-red-600">{id}</div>
                <div className="text-xs text-muted">
                  ID not found in selected genome
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="mt-6 flex items-center justify-between">
        <button
          type="button"
          onClick={() => setView("input")}
          className="inline-flex h-11 items-center justify-center rounded-lg border border-border bg-card px-5 text-sm font-semibold text-label shadow-card"
        >
          ← Edit IDs
        </button>
        {foundCount > 0 && (
          <button
            type="button"
            onClick={handleAdd}
            className="inline-flex h-11 items-center justify-center rounded-lg bg-primary px-5 text-sm font-semibold text-white shadow-card"
          >
            Add {selected.size} {selected.size === 1 ? "gene" : "genes"} to
            list →
          </button>
        )}
      </div>
    </div>
  );
}
