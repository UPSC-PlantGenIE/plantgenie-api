import { useAppDispatch, useAppSelector } from '../../../store/hooks'
import { back, next, setGenomeId } from '../../../store/wizardSlice'

const genomes = [
  {
    id: 'pinus-sylvestris-v2',
    taxonId: 'pinus-sylvestris',
    name: 'Pinus sylvestris v2.0',
    subtitle: '4,891 annotated genes  ·  Default',
  },
  {
    id: 'pinus-taeda-v3-shared',
    taxonId: 'pinus-sylvestris',
    name: 'Pinus taeda v3.0 (shared)',
    subtitle: 'Used for annotation only  ·  46,232 genes',
  },
  {
    id: 'picea-abies-v1',
    taxonId: 'picea-abies',
    name: 'Picea abies v1',
    subtitle: 'placeholder',
  },
]

export default function GenomeSelector() {
  const dispatch = useAppDispatch()
  const step = useAppSelector((s) => s.wizard.step)
  const taxonId = useAppSelector((s) => s.wizard.taxonId)
  const genomeId = useAppSelector((s) => s.wizard.genomeId)

  const active = step === 3
  const canContinue = genomeId !== null
  const visible = genomes.filter((g) => g.taxonId === taxonId)
  const eyebrow = taxonId
    ? `New gene list  ·  ${taxonLabel(taxonId)}`
    : 'New gene list'

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
          {visible.map((g) => {
            const checked = g.id === genomeId
            return (
              <label
                key={g.id}
                className={`flex h-14 cursor-pointer items-center gap-3 rounded-lg border px-3 ${
                  checked
                    ? 'border-primary bg-primary-tint'
                    : 'border-border bg-card'
                }`}
              >
                <input
                  type="radio"
                  name="genome"
                  value={g.id}
                  checked={checked}
                  onChange={() => dispatch(setGenomeId(g.id))}
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
                    {g.name}
                  </div>
                  <div className="text-xs text-muted">{g.subtitle}</div>
                </div>
              </label>
            )
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

          <button
            type="button"
            disabled={!canContinue}
            onClick={() => dispatch(next())}
            className="h-11 cursor-pointer rounded-lg bg-primary px-5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            Create list →
          </button>
        </div>
      </div>
    </section>
  )
}

function taxonLabel(id: string): string {
  return id
    .split('-')
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(' ')
}
