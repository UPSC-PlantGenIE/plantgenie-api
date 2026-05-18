import { Link, useParams } from "wouter";
import {
  useGetListQuery,
  useLookupGenesQuery,
  usePatchListMutation,
} from "../../api/plantgenieApi";

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
        <Link href="/" className="hover:text-heading">
          My Lists
        </Link>
        <span className="px-2">/</span>
        <span>{data.name}</span>
      </nav>

      <article className="mt-6 rounded-xl border border-border bg-card px-6 py-5 shadow-card">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-xl font-bold text-heading">{data.name}</h1>
            {data.description && (
              <p className="mt-1 text-sm text-muted">{data.description}</p>
            )}
          </div>
          <button
            type="button"
            onClick={handleExport}
            disabled={data.memberGeneIds.length === 0}
            className="inline-flex h-9 shrink-0 items-center justify-center rounded-lg border border-border bg-card px-4 text-sm font-semibold text-label shadow-card disabled:cursor-not-allowed disabled:opacity-50"
          >
            Export
          </button>
        </div>
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
      </article>

      {data.memberGeneIds.length > 0 ? (
        <section className="mt-6 overflow-hidden rounded-xl border border-border bg-card shadow-card">
          <div
            role="row"
            className="hidden border-b border-border bg-surface px-6 py-3 text-xs font-semibold text-muted md:grid md:grid-cols-12 md:items-center md:gap-x-4"
          >
            <div className="md:col-span-4">Gene ID</div>
            <div className="md:col-span-8">Description</div>
          </div>
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
                    className="grid grid-cols-1 gap-y-1 px-6 py-4 pr-14 hover:bg-surface md:grid-cols-12 md:items-center md:gap-x-4"
                  >
                    <span className="text-sm font-semibold text-primary md:col-span-4">
                      {id}
                    </span>
                    <span className="text-sm text-muted md:col-span-8">
                      {found?.description ?? ""}
                    </span>
                  </Link>
                  <button
                    type="button"
                    onClick={() => handleRemove(id)}
                    disabled={isRemoving}
                    aria-label={`Remove ${id}`}
                    className="absolute right-3 top-1/2 inline-flex size-8 -translate-y-1/2 items-center justify-center rounded-md text-muted hover:bg-surface hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    ✕
                  </button>
                </li>
              );
            })}
          </ul>
          <div className="border-t border-border bg-surface px-6 py-3 text-xs text-muted">
            {data.geneCount} genes total
          </div>
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
          <Link
            href="#"
            className="inline-flex h-11 items-center justify-center rounded-lg border-2 border-primary bg-card px-5 text-sm font-semibold text-primary shadow-card"
          >
            🔍 Search genes
          </Link>
        </div>
      </section>
      )}
    </div>
  );
}
