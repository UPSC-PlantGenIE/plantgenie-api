import { useState } from "react";
import { Link, useLocation, useParams } from "wouter";
import Modal from "../Modal";
import SemanticSearchButton from "./SemanticSearchButton";
import { useAppDispatch } from "../../store/hooks";
import { reset } from "../../store/wizardSlice";
import {
  useCreateListMutation,
  useDeleteListMutation,
  useGetListQuery,
  useLookupGenesQuery,
  usePatchListMutation,
} from "../../api/plantgenieApi";

type Dialog = "delete" | "newList" | "leave" | null;

const secondaryButton =
  "inline-flex h-9 cursor-pointer items-center justify-center rounded-md border border-border bg-card px-4 text-xs font-semibold text-label shadow-card disabled:cursor-not-allowed disabled:opacity-50";
const primaryButton =
  "inline-flex h-9 cursor-pointer items-center justify-center rounded-md bg-primary px-4 text-xs font-semibold text-white shadow-card disabled:cursor-not-allowed disabled:opacity-50";
const dangerButton =
  "inline-flex h-9 cursor-pointer items-center justify-center rounded-md bg-red-600 px-4 text-xs font-semibold text-white shadow-card disabled:cursor-not-allowed disabled:opacity-50";

export default function ListPage() {
  const { listId } = useParams<{ listId: string }>();
  const { data, isLoading, isError } = useGetListQuery(listId);
  const { data: members } = useLookupGenesQuery(
    {
      annotationId: data?.annotationId ?? "",
      geneIds: data?.memberGeneIds ?? [],
    },
    { skip: !data || (data?.memberGeneIds.length ?? 0) === 0 }
  );
  const [patchList, { isLoading: isRemoving }] = usePatchListMutation();
  const [createList] = useCreateListMutation();
  const [deleteList] = useDeleteListMutation();
  const [, setLocation] = useLocation();
  const dispatch = useAppDispatch();

  const [selecting, setSelecting] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [dialog, setDialog] = useState<Dialog>(null);
  const [busy, setBusy] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [draftName, setDraftName] = useState("");
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");

  const closeDialog = () => {
    if (!busy) setDialog(null);
  };

  const toggleSelecting = () => {
    setSelecting((on) => !on);
    setSelected(new Set());
  };

  const toggleSelected = (geneId: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (!next.delete(geneId)) next.add(geneId);
      return next;
    });

  const handleDeleteSelected = async () => {
    if (!listId) return;
    setBusy(true);
    try {
      await patchList({
        listId,
        removeGeneIds: [...selected],
      }).unwrap();
      setDialog(null);
      toggleSelecting();
    } finally {
      setBusy(false);
    }
  };

  const handleSaveSelectedAsNewList = async () => {
    if (!data) return;
    setBusy(true);
    try {
      const { listId: newListId } = await createList({
        name: newName.trim(),
        description: newDescription.trim() || undefined,
        annotationId: data.annotationId,
        taxonName: data.taxonName,
      }).unwrap();
      await patchList({
        listId: newListId,
        addGeneIds: [...selected],
      }).unwrap();
      setDialog(null);
      setLocation(`/lists/${newListId}`);
    } finally {
      setBusy(false);
    }
  };

  const startRenaming = () => {
    setDraftName(data?.name ?? "");
    setRenaming(true);
  };

  const finishRenaming = async (save: boolean) => {
    setRenaming(false);
    const name = draftName.trim();
    if (!save || !listId || !name || name === data?.name) return;
    await patchList({ listId, name });
  };

  const handleDiscard = async () => {
    if (!listId) return;
    setBusy(true);
    try {
      await deleteList(listId).unwrap();
      setLocation("/lists");
    } finally {
      setBusy(false);
    }
  };

  const handleNewList = () => {
    // The list is already persisted; just start a fresh wizard.
    dispatch(reset());
    setLocation("/lists/new");
  };

  const handleRemove = (geneId: string) => {
    if (!listId) return;
    if (!window.confirm(`Remove ${geneId} from this list?`)) return;
    patchList({ listId, removeGeneIds: [geneId] });
  };

  const handleExport = () => {
    if (!data) return;
    const rows = data.memberGeneIds.map((id) => {
      const found = members?.found.find((g) => g.geneId === id);
      return `${id}\t${found?.description ?? ""}`;
    });
    const tsv = ["geneId\tdescription", ...rows].join("\n");
    const slug = data.name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    const date = new Date().toISOString().slice(0, 10);
    const blob = new Blob([tsv], { type: "text/tab-separated-values" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${slug}-${date}.tsv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="mx-auto w-full max-w-7xl px-6 py-8">
        <span className="sr-only" aria-live="polite">
          Loading list
        </span>
        <div className="h-32 animate-pulse rounded-xl bg-border/40" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="mx-auto w-full max-w-7xl px-6 py-8">
        <p role="alert" className="text-sm text-red-600">
          Couldn't load this list.
        </p>
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
        <span>{data.name}</span>
      </nav>

      <article className="mt-6 rounded-xl border border-border bg-card px-6 py-5 shadow-card">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            {renaming ? (
              <input
                autoFocus
                aria-label="List name"
                value={draftName}
                onChange={(e) => setDraftName(e.target.value)}
                onBlur={() => finishRenaming(true)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") finishRenaming(true);
                  if (e.key === "Escape") finishRenaming(false);
                }}
                className="h-9 w-full min-w-64 rounded-lg border border-primary bg-input px-3 text-xl font-bold text-heading outline-none"
              />
            ) : (
              <h1 className="text-xl font-bold text-heading">
                <button
                  type="button"
                  onClick={startRenaming}
                  title="Click to rename"
                  className="cursor-text text-left hover:underline hover:decoration-dotted"
                >
                  {data.name}
                </button>
              </h1>
            )}
            {data.description && (
              <p className="mt-1 text-sm text-muted">{data.description}</p>
            )}
            <div className="mt-3 flex flex-wrap gap-2">
              <span className="rounded-md bg-primary-tint px-2.5 py-1 text-xs font-medium text-primary">
                {data.taxonName}
              </span>
              <span className="rounded-md bg-primary-tint px-2.5 py-1 text-xs font-medium text-primary">
                {data.annotationId.split("-").slice(1).join("-")}
              </span>
              <span className="rounded-md bg-primary-tint px-2.5 py-1 text-xs font-medium text-primary">
                {data.geneCount} {data.geneCount === 1 ? "gene" : "genes"}
              </span>
              <span className="rounded-md bg-primary-tint px-2.5 py-1 text-xs font-medium text-primary">
                Created{" "}
                {new Date(data.createdAt + "Z").toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                })}
              </span>
            </div>
          </div>
          <div className="grid shrink-0 grid-cols-2 gap-2">
            {data.memberGeneIds.length > 0 && (
              <>
                <Link
                  href={`/lists/${listId}/genes/add-by-id`}
                  className="inline-flex h-8 items-center justify-center rounded-md bg-primary px-3 text-xs font-semibold text-white shadow-card"
                >
                  + Add by ID
                </Link>
                <SemanticSearchButton
                  listId={data.listId}
                  taxonName={data.taxonName}
                  className="inline-flex h-8 items-center justify-center rounded-md border border-primary bg-card px-3 text-xs font-semibold text-primary shadow-card"
                />
                <Link
                  href={`/lists/${listId}/heatmap`}
                  className="inline-flex h-8 items-center justify-center rounded-md border border-primary bg-card px-3 text-xs font-semibold text-primary shadow-card"
                >
                  ▦ Heatmap
                </Link>
                <button
                  type="button"
                  className="inline-flex h-8 cursor-pointer items-center justify-center rounded-md border border-primary bg-card px-3 text-xs font-semibold text-primary shadow-card"
                >
                  Network graph
                </button>
              </>
            )}
            {data.memberGeneIds.length === 0 && (
              // An empty list was never modified, so leaving discards it.
              <button
                type="button"
                onClick={handleDiscard}
                disabled={busy}
                className="inline-flex h-8 cursor-pointer items-center justify-center rounded-md border border-border bg-card px-3 text-xs font-semibold text-label shadow-card disabled:cursor-not-allowed disabled:opacity-50"
              >
                ← Go back
              </button>
            )}
            <button
              type="button"
              onClick={handleNewList}
              className={`inline-flex h-8 cursor-pointer items-center justify-center rounded-md border border-border bg-card px-3 text-xs font-semibold text-label shadow-card ${data.memberGeneIds.length > 0 ? "col-span-2" : ""}`}
            >
              + Create new list
            </button>
          </div>
        </div>
      </article>

      {data.memberGeneIds.length > 0 ? (
        <section className="mt-6 flex flex-col overflow-hidden rounded-xl border border-border bg-card shadow-card">
          <div
            role="row"
            className="relative border-b border-border bg-surface px-6 py-3 pr-14 text-xs font-semibold text-muted"
          >
            <div className="hidden md:grid md:grid-cols-12 md:items-center md:gap-x-4">
              <div className="md:col-span-4">Gene ID</div>
              <div className="md:col-span-8">Description</div>
            </div>
            <span className="md:hidden">Genes</span>
            <button
              type="button"
              onClick={toggleSelecting}
              className="absolute right-2 top-1/2 inline-flex h-7 -translate-y-1/2 cursor-pointer items-center rounded-md border border-border bg-card px-2 text-xs font-semibold text-label"
            >
              {selecting ? "Cancel" : "Select"}
            </button>
          </div>
          <div className="max-h-[60vh] overflow-y-auto">
            <ul>
              {data.memberGeneIds.map((id) => {
                const found = members?.found.find((g) => g.geneId === id);
                return (
                  <li
                    key={id}
                    className="relative border-b border-border last:border-b-0"
                  >
                    <Link
                      href={`/genes/${data.annotationId}/${id}`}
                      state={{ listId: data.listId, listName: data.name }}
                      onClick={(e) => {
                        if (!selecting) return;
                        e.preventDefault();
                        toggleSelected(id);
                      }}
                      className={`grid grid-cols-1 gap-y-1 px-6 py-4 pr-14 hover:bg-surface md:grid-cols-12 md:items-center md:gap-x-4 ${selecting && selected.has(id) ? "bg-primary-tint" : ""}`}
                    >
                      <span className="text-sm font-semibold text-primary md:col-span-4">
                        {id}
                      </span>
                      <span className="text-sm text-muted md:col-span-8">
                        {found?.description ?? ""}
                      </span>
                    </Link>
                    {selecting ? (
                      <input
                        type="checkbox"
                        checked={selected.has(id)}
                        onChange={() => toggleSelected(id)}
                        aria-label={`Select ${id}`}
                        className="absolute right-5 top-1/2 size-5 -translate-y-1/2 cursor-pointer accent-primary"
                      />
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleRemove(id)}
                        disabled={isRemoving}
                        aria-label={`Remove ${id}`}
                        className="absolute right-3 top-1/2 inline-flex size-8 -translate-y-1/2 items-center justify-center rounded-md text-muted hover:bg-surface hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        ✕
                      </button>
                    )}
                  </li>
                );
              })}
            </ul>
            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border bg-surface px-6 py-4">
              <button
                type="button"
                onClick={() => setDialog("leave")}
                className={secondaryButton}
              >
                ← Go back
              </button>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={handleExport}
                  className={secondaryButton}
                >
                  Export
                </button>
                <button
                  type="button"
                  onClick={() => setLocation("/lists")}
                  className={primaryButton}
                >
                  Save the list
                </button>
              </div>
            </div>
          </div>
          {selecting && selected.size > 0 && (
            <div
              role="toolbar"
              aria-label="Selected genes"
              className="flex flex-wrap items-center justify-between gap-2 border-t border-border bg-card px-6 py-3 shadow-card"
            >
              <div className="flex items-center gap-3 text-xs text-label">
                <span className="font-semibold">{selected.size} selected</span>
                {selected.size < data.memberGeneIds.length && (
                  <button
                    type="button"
                    onClick={() => setSelected(new Set(data.memberGeneIds))}
                    className="cursor-pointer font-semibold text-primary"
                  >
                    Select all
                  </button>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setDialog("delete")}
                  className={dangerButton}
                >
                  Delete genes
                </button>
                <button
                  type="button"
                  onClick={() => setDialog("newList")}
                  className={primaryButton}
                >
                  Export as new list
                </button>
              </div>
            </div>
          )}
        </section>
      ) : (
        <section className="mt-6 flex flex-col items-center gap-3 rounded-2xl border-2 border-dashed border-border bg-card/50 px-6 py-16 text-center">
          <div className="flex size-20 items-center justify-center rounded-full bg-primary-tint">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 -960 960 960"
              fill="currentColor"
              className="size-8 text-primary"
            >
              <path d="M680-40v-120H560v-80h120v-120h80v120h120v80H760v120h-80ZM200-200v-560 560Zm0 80q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v353q-18-11-38-18t-42-11v-324H200v560h280q0 21 3 41t10 39H200Zm148.5-171.5Q360-303 360-320t-11.5-28.5Q337-360 320-360t-28.5 11.5Q280-337 280-320t11.5 28.5Q303-280 320-280t28.5-11.5Zm0-160Q360-463 360-480t-11.5-28.5Q337-520 320-520t-28.5 11.5Q280-497 280-480t11.5 28.5Q303-440 320-440t28.5-11.5Zm0-160Q360-623 360-640t-11.5-28.5Q337-680 320-680t-28.5 11.5Q280-657 280-640t11.5 28.5Q303-600 320-600t28.5-11.5ZM440-440h240v-80H440v80Zm0-160h240v-80H440v80Zm0 320h54q8-23 20-43t28-37H440v80Z" />
            </svg>
          </div>
          <h2 className="text-base font-semibold text-heading">
            This list has no genes yet
          </h2>
          <p className="max-w-md text-sm text-muted">
            Add genes by pasting IDs, or use keyword search to find genes by
            function or annotation.
          </p>
          <div className="mt-3 flex flex-wrap justify-center gap-3">
            <Link
              href={`/lists/${listId}/genes/add-by-id`}
              className="inline-flex h-11 items-center justify-center rounded-lg bg-primary px-5 text-sm font-semibold text-white shadow-card"
            >
              + Add by ID
            </Link>
            <SemanticSearchButton
              listId={data.listId}
              taxonName={data.taxonName}
              className="inline-flex h-11 items-center justify-center rounded-lg border-2 border-primary bg-card px-5 text-sm font-semibold text-primary shadow-card"
            />
          </div>
        </section>
      )}

      {dialog === "delete" && (
        <Modal title="Delete genes?" onClose={closeDialog}>
          <p className="mt-2 text-sm text-muted">
            Remove {selected.size} {selected.size === 1 ? "gene" : "genes"} from
            this list? This can't be undone.
          </p>
          <div className="mt-5 flex justify-end gap-2">
            <button
              type="button"
              onClick={closeDialog}
              disabled={busy}
              className={secondaryButton}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleDeleteSelected}
              disabled={busy}
              className={dangerButton}
            >
              Delete
            </button>
          </div>
        </Modal>
      )}

      {dialog === "newList" && (
        <Modal title="Save as new list" onClose={closeDialog}>
          <p className="mt-2 text-sm text-muted">
            {selected.size} {selected.size === 1 ? "gene" : "genes"} will be
            copied to a new {data.taxonName} list.
          </p>
          <label
            htmlFor="new-list-name"
            className="mt-4 block text-xs font-medium text-label"
          >
            List name
          </label>
          <input
            id="new-list-name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="mt-2 block h-11 w-full rounded-lg border border-border bg-input px-3 text-sm outline-none"
          />
          <div className="mt-4 flex items-baseline justify-between">
            <label
              htmlFor="new-list-description"
              className="text-xs font-medium text-label"
            >
              Description
            </label>
            <span className="text-xs text-muted">Optional</span>
          </div>
          <textarea
            id="new-list-description"
            value={newDescription}
            onChange={(e) => setNewDescription(e.target.value)}
            className="mt-2 block h-24 w-full resize-none rounded-lg border border-border bg-input px-3 py-3 text-sm outline-none"
          />
          <div className="mt-5 flex justify-end gap-2">
            <button
              type="button"
              onClick={closeDialog}
              disabled={busy}
              className={secondaryButton}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSaveSelectedAsNewList}
              disabled={busy || newName.trim().length === 0}
              className={primaryButton}
            >
              Save list
            </button>
          </div>
        </Modal>
      )}

      {dialog === "leave" && (
        <Modal title="Leave this list?" onClose={closeDialog}>
          <p className="mt-2 text-sm text-muted">
            Save keeps "{data.name}" in My Lists. Discard permanently deletes
            it.
          </p>
          <div className="mt-5 flex justify-end gap-2">
            <button
              type="button"
              onClick={closeDialog}
              disabled={busy}
              className={secondaryButton}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleDiscard}
              disabled={busy}
              className={dangerButton}
            >
              Discard
            </button>
            <button
              type="button"
              onClick={() => setLocation("/lists")}
              disabled={busy}
              className={primaryButton}
            >
              Save
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
