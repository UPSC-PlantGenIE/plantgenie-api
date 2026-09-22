import { useLocation } from "wouter";
import {
  useCreateListMutation,
  useGetAnnotationsQuery,
  useGetAssembliesQuery,
  useGetTaxaQuery,
} from "../../../api/plantgenieApi";
import { useAppDispatch, useAppSelector } from "../../../store/hooks";
import {
  back,
  reset,
  setDescription,
  setName,
} from "../../../store/wizardSlice";

export default function ListName() {
  const [createList] = useCreateListMutation();
  const [, setLocation] = useLocation();
  const dispatch = useAppDispatch();
  const step = useAppSelector((s) => s.wizard.step);
  const name = useAppSelector((s) => s.wizard.name);
  const description = useAppSelector((s) => s.wizard.description);
  const taxonId = useAppSelector((s) => s.wizard.taxonId);
  const annotationId = useAppSelector((s) => s.wizard.annotationId);

  const { data: taxa } = useGetTaxaQuery();
  const { data: assemblies } = useGetAssembliesQuery(
    { taxon: taxonId ?? undefined },
    { skip: !taxonId }
  );
  const { data: annotations } = useGetAnnotationsQuery(
    { taxon: taxonId ?? undefined },
    { skip: !taxonId }
  );

  const selectedTaxon = taxa?.find((taxon) => taxon.abbreviation === taxonId);
  const selectedAnnotation = annotations?.find(
    (annotation) => annotation.id === annotationId
  );
  const selectedAssembly = assemblies?.find(
    (assembly) => assembly.id === selectedAnnotation?.assemblyId
  );

  const eyebrow = [
    "New gene list",
    selectedTaxon?.scientificName,
    selectedAssembly?.version,
    selectedAnnotation?.version,
  ]
    .filter(Boolean)
    .join("  ·  ");

  const active = step === 3;
  const canCreate = name.trim().length > 0;

  const handleCreateList = async () => {
    const { listId } = await createList({
      name,
      description,
      annotationId: annotationId!,
      taxonName: selectedTaxon?.scientificName ?? "",
    }).unwrap();
    setLocation(`/lists/${listId}`);
    dispatch(reset());
  };

  return (
    <section
      className="w-screen shrink-0"
      aria-hidden={!active}
      inert={!active}
    >
      <div className="mx-auto w-full max-w-lg px-4 pt-20 pb-8">
        <p className="text-sm font-medium text-muted">{eyebrow}</p>
        <h1 className="mt-1 text-2xl font-bold text-heading">Name your list</h1>

        <div className="mt-2 flex gap-3">
          <span className="size-2 rounded-full bg-border" />
          <span className="size-2 rounded-full bg-border" />
          <span className="size-2 rounded-full bg-primary" />
        </div>

        <div className="mt-5 rounded-2xl border border-border bg-card p-7 shadow-card">
          <label
            htmlFor="list-name"
            className="block text-xs font-medium text-label"
          >
            List name
          </label>
          <input
            id="list-name"
            placeholder="e.g. Drought-response TFs in Pinus sylvestris"
            value={name}
            onChange={(e) => dispatch(setName(e.target.value))}
            className="mt-2 block h-11 w-full rounded-lg border border-border bg-input px-3 text-sm outline-none"
          />

          <div className="mt-6 flex items-baseline justify-between">
            <label
              htmlFor="description"
              className="text-xs font-medium text-label"
            >
              Description
            </label>
            <span className="text-xs text-muted">Optional</span>
          </div>
          <textarea
            id="description"
            placeholder="Optional — briefly describe the purpose of this list"
            value={description}
            onChange={(e) => dispatch(setDescription(e.target.value))}
            className="mt-2 block h-24 w-full resize-none rounded-lg border border-border bg-input px-3 py-3 text-sm outline-none"
          />
        </div>

        <div className="mt-6 flex items-center justify-between">
          <button
            type="button"
            onClick={() => dispatch(back())}
            className="h-11 cursor-pointer rounded-lg border border-border bg-card px-5 text-sm font-semibold text-label"
          >
            ← Back
          </button>

          <button
            type="button"
            disabled={!canCreate}
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
