import type { ReactNode } from 'react'
import { useAppDispatch, useAppSelector } from '../store/hooks'
import { back, next } from '../store/wizardSlice'
import ListDetails from './ListDetails'
import SelectTaxon from './SelectTaxon'
import SelectGenome from './SelectGenome'

export default function Wizard() {
  const dispatch = useAppDispatch()
  const step = useAppSelector((s) => s.wizard.step)
  const name = useAppSelector((s) => s.wizard.name)
  const taxonId = useAppSelector((s) => s.wizard.taxonId)
  const genomeId = useAppSelector((s) => s.wizard.genomeId)

  const taxonEyebrow = taxonId
    ? `New gene list  ·  ${taxonLabel(taxonId)}`
    : 'New gene list'

  const onBack = () => dispatch(back())
  const onContinue = () => dispatch(next())

  return (
    <div className="w-screen overflow-hidden">
      <div
        className="flex transition-transform duration-300 ease-in-out"
        style={{
          width: '300vw',
          transform: `translateX(-${(step - 1) * 100}vw)`,
        }}
      >
        <Panel
          stepN={1}
          active={step === 1}
          eyebrow="New gene list"
          title="Name your list"
          continueLabel="Continue →"
          canContinue={name.trim().length > 0}
          onBack={onBack}
          onContinue={onContinue}
        >
          <ListDetails />
        </Panel>

        <Panel
          stepN={2}
          active={step === 2}
          eyebrow="New gene list"
          title="Select a taxon"
          continueLabel="Continue →"
          canContinue={taxonId !== null}
          onBack={onBack}
          onContinue={onContinue}
        >
          <SelectTaxon />
        </Panel>

        <Panel
          stepN={3}
          active={step === 3}
          eyebrow={taxonEyebrow}
          title="Select a genome"
          continueLabel="Create list →"
          canContinue={genomeId !== null}
          footnote="The genome cannot be changed after the list is created."
          onBack={onBack}
          onContinue={onContinue}
        >
          <SelectGenome />
        </Panel>
      </div>
    </div>
  )
}

function Panel({
  stepN,
  active,
  eyebrow,
  title,
  continueLabel,
  canContinue,
  footnote,
  onBack,
  onContinue,
  children,
}: {
  stepN: 1 | 2 | 3
  active: boolean
  eyebrow: string
  title: string
  continueLabel: string
  canContinue: boolean
  footnote?: string
  onBack: () => void
  onContinue: () => void
  children: ReactNode
}) {
  return (
    <section
      className="w-screen shrink-0"
      aria-hidden={!active}
      inert={!active}
    >
      <div className="mx-auto w-full max-w-lg px-4 pt-20 pb-8">
        <p className="text-sm font-medium text-muted">{eyebrow}</p>
        <h1 className="mt-1 text-2xl font-bold text-heading">{title}</h1>

        <div className="mt-2 flex gap-3">
          {[1, 2, 3].map((i) => (
            <span
              key={i}
              className={`size-2 rounded-full ${
                i === stepN ? 'bg-primary' : 'bg-border'
              }`}
            />
          ))}
        </div>

        <div className="mt-5">{children}</div>

        {footnote && <p className="mt-4 text-xs text-muted">{footnote}</p>}

        <div className="mt-6 flex items-center justify-between">
          {stepN > 1 ? (
            <button
              type="button"
              onClick={onBack}
              className="h-11 cursor-pointer rounded-lg border border-border bg-card px-5 text-sm font-semibold text-label"
            >
              ← Back
            </button>
          ) : (
            <span />
          )}

          <button
            type="button"
            disabled={!canContinue}
            onClick={onContinue}
            className="h-11 cursor-pointer rounded-lg bg-primary px-5 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
          >
            {continueLabel}
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
