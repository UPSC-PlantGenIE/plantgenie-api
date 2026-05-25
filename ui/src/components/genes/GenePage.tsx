import { Link, useParams } from "wouter";
import {
  type GoTerm,
  useGetAnnotationQuery,
  useGetGeneGoTermsQuery,
  useGetGeneQuery,
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
  const { data: gene } = useGetGeneQuery({ annotationId, geneId });
  const navState = (window.history.state ?? {}) as GeneNavState;
  const length =
    gene?.startPosition != null && gene?.endPosition != null
      ? gene.endPosition - gene.startPosition + 1
      : null;

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
        <div className="mt-3 flex flex-wrap gap-2">
          {annotation && (
            <>
              <span className="rounded-md bg-primary-tint px-2.5 py-1 text-xs font-medium text-primary">
                {annotation.taxonScientificName}
              </span>
              <span className="rounded-md bg-primary-tint px-2.5 py-1 text-xs font-medium text-primary">
                {annotation.version}
              </span>
            </>
          )}
          {gene?.chromosome && (
            <span className="rounded-md bg-primary-tint px-2.5 py-1 text-xs font-medium text-primary">
              {gene.chromosome}
            </span>
          )}
        </div>
      </article>

      <div className="mt-6 space-y-6">
        <PlaceholderCard heading="Genome browser" />
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <AnnotationDetailsCard gene={gene} length={length} />
          <PlaceholderCard heading="Best Arabidopsis hit" />
        </div>
        <PlaceholderCard heading="Best hits in other taxa" />
        <GoTermsCard annotationId={annotationId} geneId={geneId} />
      </div>
    </div>
  );
}

function AnnotationDetailsCard({
  gene,
  length,
}: {
  gene:
    | {
        chromosome: string | null;
        startPosition: number | null;
        endPosition: number | null;
        strand: string | null;
      }
    | undefined;
  length: number | null;
}) {
  return (
    <section className="rounded-xl border border-border bg-card px-6 py-5 shadow-card">
      <h2 className="text-sm font-semibold text-heading">
        Annotation details
      </h2>
      <dl className="mt-3 grid grid-cols-[max-content_1fr] gap-x-4 gap-y-2 text-xs">
        <dt className="text-muted">Chromosome</dt>
        <dd className="text-heading">{gene?.chromosome ?? "—"}</dd>
        <dt className="text-muted">Position</dt>
        <dd className="text-heading">
          {gene?.startPosition != null && gene?.endPosition != null
            ? `${gene.startPosition.toLocaleString()}–${gene.endPosition.toLocaleString()}`
            : "—"}
        </dd>
        <dt className="text-muted">Length</dt>
        <dd className="text-heading">
          {length != null ? `${length.toLocaleString()} bp` : "—"}
        </dd>
        <dt className="text-muted">Strand</dt>
        <dd className="text-heading">{gene?.strand ?? "—"}</dd>
      </dl>
    </section>
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

const NAMESPACE_ORDER: GoTerm["namespace"][] = [
  "biological_process",
  "molecular_function",
  "cellular_component",
];

const NAMESPACE_META: Record<
  string,
  { label: string; abbr: string; text: string; bg: string }
> = {
  biological_process: {
    label: "Biological Process",
    abbr: "BP",
    text: "text-namespace-bp",
    bg: "bg-namespace-bp/10",
  },
  molecular_function: {
    label: "Molecular Function",
    abbr: "MF",
    text: "text-namespace-mf",
    bg: "bg-namespace-mf/10",
  },
  cellular_component: {
    label: "Cellular Component",
    abbr: "CC",
    text: "text-namespace-cc",
    bg: "bg-namespace-cc/10",
  },
};

function GoTermsCard({
  annotationId,
  geneId,
}: {
  annotationId: string;
  geneId: string;
}) {
  const { data: terms = [] } = useGetGeneGoTermsQuery({
    annotationId,
    geneId,
  });
  const grouped = NAMESPACE_ORDER.map((ns) => ({
    namespace: ns,
    terms: terms.filter((t) => t.namespace === ns),
  })).filter((g) => g.terms.length > 0);

  return (
    <section className="rounded-xl border border-border bg-card shadow-card">
      <header className="flex items-baseline gap-2 px-6 py-5">
        <h2 className="text-sm font-semibold text-heading">GO terms</h2>
        <span className="text-xs text-muted">
          {terms.length} annotation{terms.length === 1 ? "" : "s"}
        </span>
      </header>
      <div className="max-h-96 overflow-auto border-t border-border">
        {grouped.length === 0 ? (
          <p className="px-6 py-5 text-xs text-muted">
            No GO terms annotated for this gene.
          </p>
        ) : (
          grouped.map(({ namespace, terms: nsTerms }) => {
            const meta = NAMESPACE_META[namespace as string];
            return (
              <section key={namespace}>
                <h3 className="sticky top-0 z-10 flex items-baseline justify-between border-b border-border bg-surface px-6 py-2 text-xs font-semibold text-heading">
                  <span>{meta.label}</span>
                  <span className="text-muted">{nsTerms.length}</span>
                </h3>
                <ul>
                  {nsTerms.map((term, idx) => (
                    <li
                      key={term.id}
                      className={`flex items-center gap-4 border-b border-border px-6 py-2 ${
                        idx % 2 === 1 ? "bg-surface/40" : ""
                      }`}
                    >
                      <span
                        className={`inline-flex h-5 w-8 shrink-0 items-center justify-center rounded text-[10px] font-bold ${meta.bg} ${meta.text}`}
                      >
                        {meta.abbr}
                      </span>
                      <span
                        className={`shrink-0 font-mono text-xs font-semibold ${meta.text}`}
                      >
                        {term.id}
                      </span>
                      <span className="flex-1 text-xs text-label">
                        {term.name}
                      </span>
                    </li>
                  ))}
                </ul>
              </section>
            );
          })
        )}
      </div>
    </section>
  );
}
