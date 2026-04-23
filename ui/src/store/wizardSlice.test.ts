import { describe, it, expect } from 'vitest'
import reducer, {
  back,
  next,
  setGenomeId,
  setTaxonId,
  type WizardState,
} from './wizardSlice'

const baseState: WizardState = {
  step: 1,
  name: '',
  description: '',
  taxonId: null,
  genomeId: null,
}

describe('wizardSlice', () => {
  it('advances step with next()', () => {
    const s1 = reducer(baseState, next())
    expect(s1.step).toBe(2)
    const s2 = reducer(s1, next())
    expect(s2.step).toBe(3)
  })

  it('clamps next() at step 3', () => {
    const atEnd = { ...baseState, step: 3 as const }
    expect(reducer(atEnd, next()).step).toBe(3)
  })

  it('clamps back() at step 1', () => {
    expect(reducer(baseState, back()).step).toBe(1)
  })

  it('clears genomeId when taxon changes', () => {
    const state = {
      ...baseState,
      taxonId: 'pinus-sylvestris',
      genomeId: 'pinus-sylvestris-v2',
    }
    const next = reducer(state, setTaxonId('picea-abies'))
    expect(next.taxonId).toBe('picea-abies')
    expect(next.genomeId).toBeNull()
  })

  it('keeps genomeId when taxon is re-selected to the same value', () => {
    const state = {
      ...baseState,
      taxonId: 'pinus-sylvestris',
      genomeId: 'pinus-sylvestris-v2',
    }
    const next = reducer(state, setTaxonId('pinus-sylvestris'))
    expect(next.taxonId).toBe('pinus-sylvestris')
    expect(next.genomeId).toBe('pinus-sylvestris-v2')
  })

  it('setGenomeId updates genomeId only', () => {
    const state = { ...baseState, taxonId: 'pinus-sylvestris' }
    const next = reducer(state, setGenomeId('pinus-sylvestris-v2'))
    expect(next.genomeId).toBe('pinus-sylvestris-v2')
    expect(next.taxonId).toBe('pinus-sylvestris')
  })
})
