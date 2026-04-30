import { Link } from "wouter";
import { useGetMyListsQuery } from "../../api/plantgenieApi";

export default function MyListsPage() {
  const { data, isLoading } = useGetMyListsQuery();
  const lists = data ?? [];

  return (
    <div className="mx-auto w-full max-w-7xl px-6 py-12">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-heading">My lists</h1>
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
        <ul className="mt-8 flex flex-col gap-2">
          {lists.map((list) => (
            <li key={list.listId}>
              <Link
                href={`/lists/${list.listId}`}
                className="flex items-center justify-between rounded-xl border border-border bg-card px-5 py-4 shadow-card hover:border-primary"
              >
                <span className="text-sm font-semibold text-heading">
                  {list.name}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
