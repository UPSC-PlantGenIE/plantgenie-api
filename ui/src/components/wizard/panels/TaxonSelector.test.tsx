import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithStore } from '../../../test-utils'
import TaxonSelector from './TaxonSelector'

const step2State = {
  step: 2 as const,
  name: '',
  description: '',
  taxonId: null,
  genomeId: null,
}

describe('TaxonSelector', () => {
  it('renders all 7 species as radios', () => {
    renderWithStore(<TaxonSelector />, {
      preloadedState: { wizard: step2State },
    })
    const radios = screen.getAllByRole('radio')
    expect(radios).toHaveLength(7)
  })

  it('marks the stored taxonId as checked', () => {
    renderWithStore(<TaxonSelector />, {
      preloadedState: {
        wizard: { ...step2State, taxonId: 'pinus-sylvestris' },
      },
    })
    expect(
      screen.getByRole('radio', { name: /pinus sylvestris/i }),
    ).toBeChecked()
  })

  it('clicking a radio dispatches setTaxonId', async () => {
    const user = userEvent.setup()
    const { store } = renderWithStore(<TaxonSelector />, {
      preloadedState: { wizard: step2State },
    })
    await user.click(screen.getByRole('radio', { name: /picea abies/i }))
    expect(store.getState().wizard.taxonId).toBe('picea-abies')
  })

  it('changing taxon clears any existing genomeId', async () => {
    const user = userEvent.setup()
    const { store } = renderWithStore(<TaxonSelector />, {
      preloadedState: {
        wizard: {
          ...step2State,
          taxonId: 'pinus-sylvestris',
          genomeId: 'pinus-sylvestris-v2',
        },
      },
    })
    await user.click(screen.getByRole('radio', { name: /picea abies/i }))
    expect(store.getState().wizard.genomeId).toBeNull()
  })

  it('re-selecting the same taxon preserves genomeId', async () => {
    const user = userEvent.setup()
    const { store } = renderWithStore(<TaxonSelector />, {
      preloadedState: {
        wizard: {
          ...step2State,
          taxonId: 'pinus-sylvestris',
          genomeId: 'pinus-sylvestris-v2',
        },
      },
    })
    await user.click(screen.getByRole('radio', { name: /pinus sylvestris/i }))
    expect(store.getState().wizard.genomeId).toBe('pinus-sylvestris-v2')
  })
})
