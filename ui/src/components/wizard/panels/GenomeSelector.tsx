import { useEffect } from "react";
import {
  useCreateListMutation,
  useGetAnnotationsQuery,
  useGetAssembliesQuery,
  useGetTaxaQuery,
} from "../../../api/plantgenieApi";
import { useAppDispatch, useAppSelector } from "../../../store/hooks";
import { back, setAnnotationId } from "../../../store/wizardSlice";
import { useLocation } from "wouter";

const numberFmt = new Intl.NumberFormat("en-US");

export default function GenomeSelector() {
  const [createList] = useCreateListMutation();
  const [, setLocation] = useLocation();
  const dispatch = useAppDispatch();
  const accountId = useAppSelector((s) => s.account.accountId);
  const listName = useAppSelector((s) => s.wizard.name);
  const listDescription = useAppSelector((s) => s.wizard.description);
  const step = useAppSelector((s) => s.wizard.step);
  const taxonId = useAppSelector((s) => s.wizard.taxonId);
  const annotationId = useAppSelector((s) => s.wizard.annotationId);

  const handleCreateList = async () => {
    const { listId } = await createList({
      accountId: accountId ?? undefined,
      name: listName,
      description: listDescription,
      annotationId: annotationId!,
    }).unwrap();
    setLocation(`/lists/${listId}`);
  };

  const { data: taxa } = useGetTaxaQuery();
  const {
    data: assemblies,
    isLoading: assembliesLoading,
    isError: assembliesError,
  } = useGetAssembliesQuery(
    { taxon: taxonId ?? undefined },
    { skip: !taxonId }
  );
  const {
    data: annotations,
    isLoading: annotationsLoading,
    isError: annotationsError,
  } = useGetAnnotationsQuery(
    { taxon: taxonId ?? undefined },
    { skip: !taxonId }
  );

  const active = step === 3;
  const isLoading = assembliesLoading || annotationsLoading;
  const isError = assembliesError || annotationsError;
  const canContinue = annotationId !== null && !isLoading;

  const selectedTaxon = taxa?.find((t) => t.abbreviation === taxonId);
  const assemblyById = new Map((assemblies ?? []).map((a) => [a.id, a]));
  const rows = (annotations ?? []).map((n) => ({
    annotation: n,
    assembly: assemblyById.get(n.assemblyId),
  }));

  useEffect(() => {
    if (!annotations || annotations.length === 0) return;
    const currentIsValid =
      annotationId !== null && annotations.some((n) => n.id === annotationId);
    if (currentIsValid) return;
    const def = annotations.find((n) => n.isDefault) ?? annotations[0];
    dispatch(setAnnotationId(def.id));
  }, [annotationId, annotations, dispatch]);

  const eyebrow = selectedTaxon
    ? `New gene list  ·  ${selectedTaxon.scientificName}`
    : "New gene list";

  return (
    <section
      className="w-screen shrink-0"
      aria-hidden={!active}
      inert={!active}
    >
      <div className="mx-auto w-full max-w-lg px-4 pt-20 pb-8">
        <p className="text-sm font-medium text-muted">{eyebrow}</p>
        <h1 className="mt-1 text-2xl font-bold text-heading">
          Select a genome
        </h1>

        <div className="mt-2 flex gap-3">
          <span className="size-2 rounded-full bg-border" />
          <span className="size-2 rounded-full bg-border" />
          <span className="size-2 rounded-full bg-primary" />
        </div>

        <div className="mt-5 flex flex-col gap-2 rounded-2xl border border-border bg-card p-5 shadow-card">
          {isLoading && (
            <>
              <span className="sr-only" aria-live="polite">
                Loading genomes
              </span>
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  aria-hidden
                  className="h-14 animate-pulse rounded-lg bg-border/40"
                />
              ))}
            </>
          )}

          {isError && (
            <p role="alert" className="text-sm text-red-600">
              Couldn't load genomes. Please try again.
            </p>
          )}

          {!isLoading && !isError && rows.length === 0 && (
            <p className="text-sm text-muted">No genomes available</p>
          )}

          {!isLoading &&
            !isError &&
            rows.map(({ annotation, assembly }) => {
              const checked = annotation.id === annotationId;
              const title = assembly
                ? `Genome - ${assembly.version}  ·  Annotation - ${annotation.version}`
                : `Annotation ${annotation.version}`;
              const subtitle = `${numberFmt.format(annotation.geneCount)} genes${
                annotation.isDefault ? "  ·  Default" : ""
              }`;
              return (
                <label
                  key={annotation.id}
                  className={`flex h-14 cursor-pointer items-center gap-3 rounded-lg border px-3 ${
                    checked
                      ? "border-primary bg-primary-tint"
                      : "border-border bg-card"
                  }`}
                >
                  <input
                    type="radio"
                    name="genome"
                    value={annotation.id}
                    checked={checked}
                    onChange={() => dispatch(setAnnotationId(annotation.id))}
                    className="sr-only"
                  />
                  <span
                    className={`flex size-5 items-center justify-center rounded-full border ${
                      checked ? "border-primary" : "border-border"
                    }`}
                  >
                    {checked && (
                      <span className="size-2 rounded-full bg-primary" />
                    )}
                  </span>
                  <div>
                    <div
                      className={`text-sm text-heading ${
                        checked ? "font-semibold" : "font-medium"
                      }`}
                    >
                      {title}
                    </div>
                    <div className="text-xs text-muted">{subtitle}</div>
                  </div>
                </label>
              );
            })}
        </div>

        <p className="mt-4 text-xs text-muted">
          The genome cannot be changed after the list is created.
        </p>

        <div className="mt-6 flex items-center justify-between">
          <button
            type="button"
            onClick={() => dispatch(back())}
            className="h-11 cursor-pointer rounded-lg border border-border bg-card px-5 text-sm font-semibold text-label"
          >
            ← Back
          </button>

          {/* TODO: replace dispatch(next()) with the create-list flow:
              1. call useCreateListMutation() at the top of this component
              2. on click, await createList({ accountId, name, description, annotationId, geneIds: [] }).unwrap()
              3. read setLocation from wouter's useLocation() and call setLocation(`/lists/${response.listId}`)
              4. delete the dispatch(next()) line — it no longer makes sense since step caps at 3 */}
          <button
            type="button"
            disabled={!canContinue}
            onClick={handleCreateList}
            className="h-11 cursor-pointer rounded-lg bg-primary px-5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            Create list →
          </button>
        </div>
      </div>
    </section>
  );
}
