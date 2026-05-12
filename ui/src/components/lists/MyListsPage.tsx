import { Link } from "wouter";
import { useGetMyListsQuery } from "../../api/plantgenieApi";

const dateFmt = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  year: "numeric",
});

const formatDate = (iso: string) =>
  dateFmt.format(new Date(iso.endsWith("Z") ? iso : iso + "Z"));

const genomeVersion = (annotationId: string) =>
  annotationId.split("-").slice(1).join("-");

export default function MyListsPage() {
  const { data, isLoading } = useGetMyListsQuery();
  const lists = data ?? [];

  return (
    <div className="mx-auto w-full max-w-7xl px-6 py-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-heading">My Lists</h1>
          {lists.length > 0 && (
            <p className="mt-1 text-sm text-muted">
              {lists.length} {lists.length === 1 ? "list" : "lists"}
            </p>
          )}
        </div>
        <Link
          href="/lists/new"
          className="inline-flex h-10 items-center justify-center rounded-lg bg-primary px-5 text-sm font-semibold text-white shadow-card"
        >
          + New list
        </Link>
      </div>

      {isLoading ? (
        <div className="mt-8 flex flex-col gap-2">
          <span className="sr-only" aria-live="polite">
            Loading lists
          </span>
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              aria-hidden
              className="h-16 animate-pulse rounded-xl bg-border/40"
            />
          ))}
        </div>
      ) : lists.length === 0 ? (
        <div className="mt-8 flex flex-col items-center gap-4 rounded-2xl border-2 border-dashed border-border bg-card/50 px-6 py-16">
          <div className="flex size-20 items-center justify-center rounded-full bg-primary-tint">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 -960 960 960"
              className="size-6 text-primary"
              fill="currentColor"
            >
              <path d="M680-40v-120H560v-80h120v-120h80v120h120v80H760v120h-80ZM200-200v-560 560Zm0 80q-33 0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 56.5 23.5T840-760v353q-18-11-38-18t-42-11v-324H200v560h280q0 21 3 41t10 39H200Zm148.5-171.5Q360-303 360-320t-11.5-28.5Q337-360 320-360t-28.5 11.5Q280-337 280-320t11.5 28.5Q303-280 320-280t28.5-11.5Zm0-160Q360-463 360-480t-11.5-28.5Q337-520 320-520t-28.5 11.5Q280-497 280-480t11.5 28.5Q303-440 320-440t28.5-11.5Zm0-160Q360-623 360-640t-11.5-28.5Q337-680 320-680t-28.5 11.5Q280-657 280-640t11.5 28.5Q303-600 320-600t28.5-11.5ZM440-440h240v-80H440v80Zm0-160h240v-80H440v80Zm0 320h54q8-23 20-43t28-37H440v80Z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-heading">No lists yet</h2>
          <p className="text-sm text-muted">
            Create your first gene list to get started.
          </p>
          <Link
            href="/lists/new"
            className="inline-flex h-11 items-center justify-center rounded-lg bg-primary px-5 text-sm font-semibold text-white shadow-card"
          >
            + Create your first list
          </Link>
        </div>
      ) : (
        <div className="mt-8 overflow-hidden rounded-xl border border-border bg-card shadow-card">
          <div
            role="row"
            className="hidden border-b border-border bg-surface px-5 py-3 text-xs font-medium text-muted md:grid md:grid-cols-12 md:items-center md:gap-x-4"
          >
            <div className="md:col-span-5">List name</div>
            <div className="md:col-span-2 md:text-center">Taxon</div>
            <div className="md:col-span-2 md:text-center">Genome</div>
            <div className="md:col-span-1 md:text-center">Genes</div>
            <div className="md:col-span-2 md:text-center">Last updated</div>
          </div>

          <ul>
            {lists.map((list) => (
              <li
                key={list.listId}
                className="border-b border-border last:border-b-0"
              >
                <Link
                  href={`/lists/${list.listId}`}
                  className="grid grid-cols-1 gap-y-2 px-5 py-4 hover:bg-surface md:grid-cols-12 md:items-center md:gap-x-4"
                >
                  <div className="text-center md:col-span-5 md:text-left">
                    <div className="text-sm font-semibold text-heading">
                      {list.name}
                    </div>
                    {list.description && (
                      <div className="mt-0.5 text-xs text-muted">
                        {list.description}
                      </div>
                    )}
                  </div>
                  <span className="inline-flex w-fit items-center justify-self-center rounded-md bg-primary-tint px-2.5 py-1 text-xs font-medium text-primary md:col-span-2">
                    {list.taxonName}
                  </span>
                  <span className="text-center text-sm text-label md:col-span-2">
                    {genomeVersion(list.annotationId)}
                  </span>
                  <span className="text-center text-sm text-label md:col-span-1">
                    {list.geneCount} {list.geneCount === 1 ? "gene" : "genes"}
                  </span>
                  <span className="text-center text-sm text-muted md:col-span-2">
                    {formatDate(list.createdAt)}
                  </span>
                </Link>
              </li>
            ))}
          </ul>

          <p className="border-t border-border bg-surface px-5 py-3 text-right text-xs text-muted">
            {lists.length} {lists.length === 1 ? "list" : "lists"} total
          </p>
        </div>
      )}
    </div>
  );
}
