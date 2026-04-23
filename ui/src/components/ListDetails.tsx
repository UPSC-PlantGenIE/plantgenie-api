import { useAppDispatch, useAppSelector } from '../store/hooks'
import { setDescription, setName } from '../store/wizardSlice'

export default function ListDetails() {
  const dispatch = useAppDispatch()
  const name = useAppSelector((s) => s.wizard.name)
  const description = useAppSelector((s) => s.wizard.description)

  return (
    <div className="rounded-2xl border border-border bg-card p-7 shadow-card">
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
  )
}
