import { useAppDispatch, useAppSelector } from '../store/hooks'
import { setTaxonId } from '../store/wizardSlice'

const taxa = [
  {
    id: 'arabidopsis-thaliana',
    name: 'Arabidopsis thaliana',
    subtitle: 'Col-0 reference',
  },
  {
    id: 'pinus-sylvestris',
    name: 'Pinus sylvestris',
    subtitle: 'Scots pine',
  },
  {
    id: 'pinus-taeda',
    name: 'Pinus taeda',
    subtitle: 'Loblolly pine',
  },
  {
    id: 'populus-tremula',
    name: 'Populus tremula',
    subtitle: 'European aspen',
  },
  {
    id: 'picea-abies',
    name: 'Picea abies',
    subtitle: 'Norway spruce',
  },
  {
    id: 'betula-pendula',
    name: 'Betula pendula',
    subtitle: 'Silver birch',
  },
  {
    id: 'eucalyptus-grandis',
    name: 'Eucalyptus grandis',
    subtitle: 'Rose gum',
  },
]

export default function SelectTaxon() {
  const dispatch = useAppDispatch()
  const taxonId = useAppSelector((s) => s.wizard.taxonId)

  return (
    <div className="flex flex-col gap-2 rounded-2xl border border-border bg-card p-5 shadow-card">
      {taxa.map((t) => {
        const checked = t.id === taxonId
        return (
          <label
            key={t.id}
            className={`flex h-14 cursor-pointer items-center gap-3 rounded-lg border px-3 ${
              checked
                ? 'border-primary bg-primary-tint'
                : 'border-border bg-card'
            }`}
          >
            <input
              type="radio"
              name="taxon"
              value={t.id}
              checked={checked}
              onChange={() => dispatch(setTaxonId(t.id))}
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
                {t.name}
              </div>
              <div className="text-xs text-muted">{t.subtitle}</div>
            </div>
          </label>
        )
      })}
    </div>
  )
}
