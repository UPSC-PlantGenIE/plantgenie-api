import { useEffect, useState } from "react";
import { useLocation, useParams } from "wouter";
import {
  useGetListQuery,
  useLookupGenesMutation,
  usePatchListMutation,
} from "../../api/plantgenieApi";

export default function AddByIdPage() {
  const { listId } = useParams<{ listId: string }>();
  const [, setLocation] = useLocation();
  const { data: list } = useGetListQuery(listId ?? "", {
    skip: !listId,
  });
  const [lookup, { data: result }] = useLookupGenesMutation();
  const [patchList] = usePatchListMutation();
  const [text, setText] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (result) {
      setSelected(new Set(result.found.map((g) => g.geneId)));
    }
  }, [result]);

  const handleValidate = async () => {
    if (!list) return;
    const geneIds = text
      .split(/[\s,]+/)
      .map((g) => g.trim())
      .filter(Boolean);
    if (geneIds.length === 0) return;
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
          {result.found.length > 0 && (
            <ul className="flex flex-col gap-2">
              {result.found.map((g) => (
                <li key={g.geneId}>
                  <label className="flex cursor-pointer items-start gap-3 rounded-lg border border-border bg-card px-4 py-3 text-sm">
                    <input
                      type="checkbox"
                      checked={selected.has(g.geneId)}
                      onChange={() => toggle(g.geneId)}
                      className="mt-1 size-4"
                    />
                    <div>
                      <div className="font-semibold text-heading">
                        {g.geneId} – {g.name}
                      </div>
                      <div className="text-xs text-muted">
                        {g.description}
                      </div>
                    </div>
                  </label>
                </li>
              ))}
            </ul>
          )}
          {result.notFound.length > 0 && (
            <p className="text-sm text-red-600">
              Not found: {result.notFound.join(", ")}
            </p>
          )}
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
