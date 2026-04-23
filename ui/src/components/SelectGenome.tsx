import { useAppDispatch, useAppSelector } from '../store/hooks'
import { setGenomeId } from '../store/wizardSlice'

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

export default function SelectGenome() {
  const dispatch = useAppDispatch()
  const taxonId = useAppSelector((s) => s.wizard.taxonId)
  const genomeId = useAppSelector((s) => s.wizard.genomeId)
  const visible = genomes.filter((g) => g.taxonId === taxonId)

  return (
    <div className="flex flex-col gap-2 rounded-2xl border border-border bg-card p-5 shadow-card">
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
              {checked && <span className="size-2 rounded-full bg-primary" />}
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
  )
}
