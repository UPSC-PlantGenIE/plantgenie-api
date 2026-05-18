import { Link, useParams } from "wouter";
import {
  useGetAnnotationQuery,
  useLookupGenesQuery,
} from "../../api/plantgenieApi";

type GeneNavState = {
  listId?: string;
  listName?: string;
};

export default function GenePage() {
  const { annotationId, geneId } = useParams<{
    annotationId: string;
    geneId: string;
  }>();
  const { data: annotation } = useGetAnnotationQuery(annotationId);
  const { data: lookup } = useLookupGenesQuery({
    annotationId,
    geneIds: [geneId],
  });
  const navState = (window.history.state ?? {}) as GeneNavState;
  const gene = lookup?.found.find((g) => g.geneId === geneId);

  return (
    <div className="mx-auto w-full max-w-7xl px-6 py-8">
      <nav className="text-xs text-muted" aria-label="Breadcrumb">
        <Link href="/" className="hover:text-heading">
          My Lists
        </Link>
        <span className="px-2">/</span>
        {navState.listId && navState.listName && (
          <>
            <Link
              href={`/lists/${navState.listId}`}
              className="hover:text-heading"
            >
              {navState.listName}
            </Link>
            <span className="px-2">/</span>
          </>
        )}
        <span>{geneId}</span>
      </nav>

      <article className="mt-6 rounded-xl border border-border bg-card px-6 py-5 shadow-card">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-xl font-bold text-heading">{geneId}</h1>
            {gene?.name && (
              <p className="mt-1 text-sm font-medium text-primary">
                {gene.name}
              </p>
            )}
            {gene?.description && (
              <p className="mt-2 max-w-3xl text-sm text-muted">
                {gene.description}
              </p>
            )}
          </div>
          <Link
            href="/"
            className="inline-flex h-9 shrink-0 items-center justify-center rounded-lg border border-border bg-card px-4 text-sm font-semibold text-label shadow-card"
          >
            ← Back to My Lists
          </Link>
        </div>
        {annotation && (
          <div className="mt-3 flex flex-wrap gap-2">
            <span className="rounded-md bg-primary-tint px-2.5 py-1 text-xs font-medium text-primary">
              {annotation.taxonScientificName}
            </span>
            <span className="rounded-md bg-primary-tint px-2.5 py-1 text-xs font-medium text-primary">
              {annotation.version}
            </span>
          </div>
        )}
      </article>

      <div className="mt-6 space-y-6">
        <PlaceholderCard heading="Genome browser" />
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <PlaceholderCard heading="Annotation details" />
          <PlaceholderCard heading="Best Arabidopsis hit" />
        </div>
        <PlaceholderCard heading="Best hits in other taxa" />
        <PlaceholderCard heading="GO terms" />
      </div>
    </div>
  );
}

function PlaceholderCard({ heading }: { heading: string }) {
  return (
    <section className="rounded-xl border border-border bg-card px-6 py-5 shadow-card">
      <h2 className="text-sm font-semibold text-heading">{heading}</h2>
      <p className="mt-2 text-xs text-muted">Coming soon</p>
    </section>
  );
}
