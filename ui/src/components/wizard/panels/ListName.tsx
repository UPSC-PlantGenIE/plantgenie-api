import { useAppDispatch, useAppSelector } from '../../../store/hooks'
import { next, setDescription, setName } from '../../../store/wizardSlice'

export default function ListName() {
  const dispatch = useAppDispatch()
  const step = useAppSelector((s) => s.wizard.step)
  const name = useAppSelector((s) => s.wizard.name)
  const description = useAppSelector((s) => s.wizard.description)

  const active = step === 1
  const canContinue = name.trim().length > 0

  return (
    <section
      className="w-screen shrink-0"
      aria-hidden={!active}
      inert={!active}
    >
      <div className="mx-auto w-full max-w-lg px-4 pt-20 pb-8">
        <p className="text-sm font-medium text-muted">New gene list</p>
        <h1 className="mt-1 text-2xl font-bold text-heading">Name your list</h1>

        <div className="mt-2 flex gap-3">
          <span className="size-2 rounded-full bg-primary" />
          <span className="size-2 rounded-full bg-border" />
          <span className="size-2 rounded-full bg-border" />
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

        <div className="mt-6 flex items-center justify-end">
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
