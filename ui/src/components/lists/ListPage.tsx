import { Link, useParams } from "wouter";
import { useGetListQuery } from "../../api/plantgenieApi";

export default function ListPage() {
  const { listId } = useParams<{ listId: string }>();
  const { data, isLoading, isError } = useGetListQuery(listId);

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

      <article className="mt-6 flex flex-col gap-4 rounded-xl border border-border bg-card px-6 py-5 shadow-card sm:flex-row sm:items-start sm:justify-between">
        <h1 className="text-xl font-bold text-heading">{data.name}</h1>
        <button
          type="button"
          className="inline-flex h-9 shrink-0 items-center justify-center rounded-lg border border-border bg-card px-4 text-sm font-semibold text-label shadow-card"
        >
          Export
        </button>
      </article>

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
            href="#"
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
    </div>
  );
}
