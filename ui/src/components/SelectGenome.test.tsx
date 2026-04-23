import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithStore } from '../test-utils'
import SelectGenome from './SelectGenome'

const pinusSylvestrisState = {
  step: 3 as const,
  name: '',
  description: '',
  taxonId: 'pinus-sylvestris',
  genomeId: null,
}

describe('SelectGenome', () => {
  it('renders only genomes for the current taxon', () => {
    renderWithStore(<SelectGenome />, {
      preloadedState: { wizard: pinusSylvestrisState },
    })
    const radios = screen.getAllByRole('radio')
    expect(radios).toHaveLength(2)
  })

  it('marks the stored genomeId as checked', () => {
    renderWithStore(<SelectGenome />, {
      preloadedState: {
        wizard: { ...pinusSylvestrisState, genomeId: 'pinus-sylvestris-v2' },
      },
    })
    expect(
      screen.getByRole('radio', { name: /pinus sylvestris v2\.0/i }),
    ).toBeChecked()
  })

  it('clicking a radio dispatches setGenomeId', async () => {
    const user = userEvent.setup()
    const { store } = renderWithStore(<SelectGenome />, {
      preloadedState: { wizard: pinusSylvestrisState },
    })
    await user.click(
      screen.getByRole('radio', { name: /pinus sylvestris v2\.0/i }),
    )
    expect(store.getState().wizard.genomeId).toBe('pinus-sylvestris-v2')
  })

  it('filters out genomes for other taxa', () => {
    renderWithStore(<SelectGenome />, {
      preloadedState: {
        wizard: { ...pinusSylvestrisState, taxonId: 'picea-abies' },
      },
    })
    expect(
      screen.queryByRole('radio', { name: /pinus sylvestris v2\.0/i }),
    ).not.toBeInTheDocument()
  })
})
