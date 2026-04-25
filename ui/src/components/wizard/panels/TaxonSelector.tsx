import { useGetTaxaQuery } from '../../../api/plantgenieApi'
import { useAppDispatch, useAppSelector } from '../../../store/hooks'
import { back, next, setTaxonId } from '../../../store/wizardSlice'

export default function TaxonSelector() {
  const dispatch = useAppDispatch()
  const step = useAppSelector((s) => s.wizard.step)
  const taxonId = useAppSelector((s) => s.wizard.taxonId)
  const { data: taxa, isLoading, isError } = useGetTaxaQuery()

  const active = step === 2
  const canContinue = taxonId !== null && !isLoading

  return (
    <section
      className="w-screen shrink-0"
      aria-hidden={!active}
      inert={!active}
    >
      <div className="mx-auto w-full max-w-lg px-4 pt-20 pb-8">
        <p className="text-sm font-medium text-muted">New gene list</p>
        <h1 className="mt-1 text-2xl font-bold text-heading">
          Select a taxon
        </h1>

        <div className="mt-2 flex gap-3">
          <span className="size-2 rounded-full bg-border" />
          <span className="size-2 rounded-full bg-primary" />
          <span className="size-2 rounded-full bg-border" />
        </div>

        <div className="mt-5 flex flex-col gap-2 rounded-2xl border border-border bg-card p-5 shadow-card">
          {isLoading && (
            <>
              <span className="sr-only" aria-live="polite">
                Loading taxa
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
              Couldn't load taxa. Please try again.
            </p>
          )}

          {!isLoading && !isError && taxa && taxa.length === 0 && (
            <p className="text-sm text-muted">No taxa available</p>
          )}

          {!isLoading &&
            !isError &&
            taxa?.map((t) => {
              const checked = t.abbreviation === taxonId
              return (
                <label
                  key={t.abbreviation}
                  className={`flex h-14 cursor-pointer items-center gap-3 rounded-lg border px-3 ${
                    checked
                      ? 'border-primary bg-primary-tint'
                      : 'border-border bg-card'
                  }`}
                >
                  <input
                    type="radio"
                    name="taxon"
                    value={t.abbreviation}
                    checked={checked}
                    onChange={() => dispatch(setTaxonId(t.abbreviation))}
                    className="sr-only"
                  />
                  <span
                    className={`flex size-5 items-center justify-center rounded-full border ${
                      checked ? 'border-primary' : 'border-border'
                    }`}
                  >
                    {checked && (
                      <span className="size-2 rounded-full bg-primary" />
                    )}
                  </span>
                  <div>
                    <div
                      className={`text-sm text-heading ${
                        checked ? 'font-semibold' : 'font-medium'
                      }`}
                    >
                      {t.scientificName}
                    </div>
                    {t.commonName && (
                      <div className="text-xs text-muted">{t.commonName}</div>
                    )}
                  </div>
                </label>
              )
            })}
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
            disabled={!canContinue}
            onClick={() => dispatch(next())}
            className="h-11 cursor-pointer rounded-lg bg-primary px-5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            Continue →
          </button>
        </div>
      </div>
    </section>
  )
}
