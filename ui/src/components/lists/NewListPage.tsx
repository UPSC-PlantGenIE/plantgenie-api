import { useState } from "react";
import { useLocation } from "wouter";
import {
  useCreateListMutation,
  useGetAnnotationsQuery,
  useGetAssembliesQuery,
  useGetTaxaQuery,
} from "../../api/plantgenieApi";
import { buttonClassName } from "../shared/buttonClassName";

const numberFormat = new Intl.NumberFormat("en-US");

const inputClassName =
  "mt-2 block w-full rounded-lg border border-border bg-input px-3 text-base sm:text-sm";

type ChoiceProps = {
  groupName: string;
  value: string;
  checked: boolean;
  onChange: () => void;
  title: string;
  subtitle?: string;
};

const Choice = ({
  groupName,
  value,
  checked,
  onChange,
  title,
  subtitle,
}: ChoiceProps) => (
  <label
    className={`flex min-h-14 cursor-pointer items-center gap-3 rounded-lg border px-3 py-2 has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-primary ${
      checked ? "border-primary bg-primary-tint" : "border-border bg-card"
    }`}
  >
    <input
      type="radio"
      name={groupName}
      value={value}
      checked={checked}
      onChange={onChange}
      className="sr-only"
    />
    <span
      className={`flex size-5 shrink-0 items-center justify-center rounded-full border ${
        checked ? "border-primary" : "border-border"
      }`}
    >
      {checked && <span className="size-2 rounded-full bg-primary" />}
    </span>
    <span className="min-w-0">
      <span
        className={`block text-sm text-heading ${
          checked ? "font-semibold" : "font-medium"
        }`}
      >
        {title}
      </span>
      {subtitle && <span className="block text-xs text-muted">{subtitle}</span>}
    </span>
  </label>
);

const LoadingChoices = ({ label }: { label: string }) => (
  <>
    <span className="sr-only" aria-live="polite">
      {label}
    </span>
    {[0, 1, 2].map((index) => (
      <div
        key={index}
        aria-hidden
        className="h-14 animate-pulse rounded-lg bg-border/40"
      />
    ))}
  </>
);

const NewListPage = () => {
  const [taxonId, setTaxonId] = useState<string | null>(null);
  const [chosenAnnotationId, setChosenAnnotationId] = useState<string | null>(
    null
  );
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [, setLocation] = useLocation();
  const [createList, { isLoading: isCreating }] = useCreateListMutation();

  const {
    data: taxa,
    isLoading: taxaLoading,
    isError: taxaError,
  } = useGetTaxaQuery();
  const {
    currentData: assemblies,
    isFetching: assembliesFetching,
    isError: assembliesError,
  } = useGetAssembliesQuery(
    { taxon: taxonId ?? undefined },
    { skip: !taxonId }
  );
  const {
    currentData: annotations,
    isFetching: annotationsFetching,
    isError: annotationsError,
  } = useGetAnnotationsQuery(
    { taxon: taxonId ?? undefined },
    { skip: !taxonId }
  );

  const genomesLoading = assembliesFetching || annotationsFetching;
  const genomesError = assembliesError || annotationsError;

  const selectedTaxon = taxa?.find((taxon) => taxon.abbreviation === taxonId);
  const assemblyById = new Map(
    (assemblies ?? []).map((assembly) => [assembly.id, assembly])
  );
  const defaultAnnotation =
    annotations?.find((annotation) => annotation.isDefault) ?? annotations?.[0];
  const annotationId =
    annotations?.find((annotation) => annotation.id === chosenAnnotationId)
      ?.id ??
    defaultAnnotation?.id ??
    null;

  const canCreate =
    annotationId !== null && name.trim().length > 0 && !isCreating;

  const handleCreateList = async () => {
    if (annotationId === null) return;
    const { listId } = await createList({
      name,
      description,
      annotationId,
      taxonName: selectedTaxon?.scientificName ?? "",
    }).unwrap();
    setLocation(`/lists/${listId}`);
  };

  return (
    <div className="mx-auto w-full max-w-lg px-4 py-6 sm:py-8">
      <h1 className="text-2xl font-bold text-heading">New gene list</h1>

      <div className="mt-5 flex flex-col gap-6 rounded-2xl border border-border bg-card p-4 shadow-card sm:p-7">
        <fieldset className="flex min-w-0 flex-col gap-2">
          <legend className="mb-2 text-sm font-semibold text-heading">
            Taxon
          </legend>

          {taxaLoading && <LoadingChoices label="Loading taxa" />}

          {taxaError && (
            <p role="alert" className="text-sm text-red-600">
              Couldn't load taxa. Please try again.
            </p>
          )}

          {!taxaLoading && !taxaError && taxa?.length === 0 && (
            <p className="text-sm text-muted">No taxa available</p>
          )}

          {!taxaLoading &&
            !taxaError &&
            taxa?.map((taxon) => (
              <Choice
                key={taxon.abbreviation}
                groupName="taxon"
                value={taxon.abbreviation}
                checked={taxon.abbreviation === taxonId}
                onChange={() => {
                  setTaxonId(taxon.abbreviation);
                  setChosenAnnotationId(null);
                }}
                title={taxon.scientificName}
                subtitle={taxon.commonName ?? undefined}
              />
            ))}
        </fieldset>

        <fieldset className="flex min-w-0 flex-col gap-2">
          <legend className="mb-2 text-sm font-semibold text-heading">
            Genome
          </legend>

          {!taxonId && (
            <p className="text-sm text-muted">
              Pick a taxon to see its genomes.
            </p>
          )}

          {taxonId && genomesLoading && (
            <LoadingChoices label="Loading genomes" />
          )}

          {taxonId && !genomesLoading && genomesError && (
            <p role="alert" className="text-sm text-red-600">
              Couldn't load genomes. Please try again.
            </p>
          )}

          {taxonId &&
            !genomesLoading &&
            !genomesError &&
            annotations?.length === 0 && (
              <p className="text-sm text-muted">No genomes available</p>
            )}

          {taxonId &&
            !genomesLoading &&
            !genomesError &&
            annotations?.map((annotation) => {
              const assembly = assemblyById.get(annotation.assemblyId);
              return (
                <Choice
                  key={annotation.id}
                  groupName="genome"
                  value={annotation.id}
                  checked={annotation.id === annotationId}
                  onChange={() => setChosenAnnotationId(annotation.id)}
                  title={
                    assembly
                      ? `Genome - ${assembly.version}  ·  Annotation - ${annotation.version}`
                      : `Annotation - ${annotation.version}`
                  }
                  subtitle={`${numberFormat.format(annotation.geneCount)} genes${
                    annotation.isDefault ? "  ·  Default" : ""
                  }`}
                />
              );
            })}

          {taxonId && (
            <p className="mt-1 text-xs text-muted">
              The genome cannot be changed after the list is created.
            </p>
          )}
        </fieldset>

        <div>
          <label
            htmlFor="list-name"
            className="block text-sm font-semibold text-heading"
          >
            List name
          </label>
          <input
            id="list-name"
            placeholder="e.g. Drought-response TFs in Pinus sylvestris"
            value={name}
            onChange={(event) => setName(event.target.value)}
            className={`${inputClassName} h-11`}
          />
        </div>

        <div>
          <div className="flex items-baseline justify-between">
            <label
              htmlFor="description"
              className="text-sm font-semibold text-heading"
            >
              Description
            </label>
            <span className="text-xs text-muted">Optional</span>
          </div>
          <textarea
            id="description"
            placeholder="Briefly describe the purpose of this list"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            className={`${inputClassName} h-24 resize-none py-3`}
          />
        </div>
      </div>

      <div className="mt-6 flex justify-end">
        <button
          type="button"
          disabled={!canCreate}
          onClick={handleCreateList}
          className={`${buttonClassName()} w-full sm:w-auto`}
        >
          Create list
        </button>
      </div>
    </div>
  );
};

export default NewListPage;
