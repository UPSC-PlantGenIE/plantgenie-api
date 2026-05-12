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

  const foundMap = new Map(result?.found.map((g) => [g.geneId, g]));
  const foundCount = result?.found.length ?? 0;
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

      {result && (
        <div className="mt-6 flex flex-col gap-4">
          {foundCount > 0 && (
            <label className="flex cursor-pointer items-center gap-3 px-4 text-sm font-semibold text-label">
              <input
                ref={selectAllRef}
                type="checkbox"
                checked={allSelected}
                onChange={toggleAll}
                className="size-4"
              />
              Select all
            </label>
          )}
          <ul className="flex flex-col gap-2">
            {orderedIds.map((id) => {
              const found = foundMap.get(id);
              if (found) {
                return (
                  <li key={id}>
                    <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border bg-card px-4 py-3 text-sm">
                      <input
                        type="checkbox"
                        checked={selected.has(found.geneId)}
                        onChange={() => toggle(found.geneId)}
                        className="mt-1 size-4"
                      />
                      <div>
                        <div className="font-semibold text-heading">
                          {found.geneId} – {found.name}
                        </div>
                        <div className="text-xs text-muted">
                          {found.description}
                        </div>
                      </div>
                    </label>
                  </li>
                );
              }
              return (
                <li key={id}>
                  <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-3 text-sm">
                    <span
                      aria-label="Not found"
                      className="inline-flex size-4 items-center justify-center text-red-600"
                    >
                      ✕
                    </span>
                    <span className="font-semibold text-red-600">{id}</span>
                  </div>
                </li>
              );
            })}
          </ul>
          {result.found.length > 0 && (
            <button
              type="button"
              onClick={handleAdd}
              className="inline-flex h-11 items-center justify-center rounded-lg bg-primary px-5 text-sm font-semibold text-white shadow-card"
            >
              Add to list
            </button>
          )}
        </div>
      )}
    </div>
  );
}
