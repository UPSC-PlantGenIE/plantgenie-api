import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithStore } from '../../../test-utils'
import GenomeSelector from './GenomeSelector'

const pinsyState = {
  step: 3 as const,
  name: '',
  description: '',
  taxonId: 'pinsy',
  annotationId: null,
}

describe('GenomeSelector', () => {
  it('renders only annotations for the current taxon', async () => {
    renderWithStore(<GenomeSelector />, {
      preloadedState: { wizard: pinsyState },
    })
    const radios = await screen.findAllByRole('radio')
    expect(radios).toHaveLength(2)
  })

  it('auto-selects the default annotation when none is chosen', async () => {
    const { store } = renderWithStore(<GenomeSelector />, {
      preloadedState: { wizard: pinsyState },
    })
    await screen.findByRole('radio', { name: /Araport11/i })
    expect(store.getState().wizard.annotationId).toBe('pinsy-Araport11')
  })

  it('marks the stored annotationId as checked', async () => {
    renderWithStore(<GenomeSelector />, {
      preloadedState: {
        wizard: { ...pinsyState, annotationId: 'pinsy-TAIR10' },
      },
    })
    expect(
      await screen.findByRole('radio', { name: /TAIR10/i }),
    ).toBeChecked()
  })

  it('clicking a radio dispatches setAnnotationId', async () => {
    const user = userEvent.setup()
    const { store } = renderWithStore(<GenomeSelector />, {
      preloadedState: { wizard: pinsyState },
    })
    await user.click(
      await screen.findByRole('radio', { name: /TAIR10/i }),
    )
    expect(store.getState().wizard.annotationId).toBe('pinsy-TAIR10')
  })

  it('filters out annotations for other taxa', async () => {
    renderWithStore(<GenomeSelector />, {
      preloadedState: { wizard: { ...pinsyState, taxonId: 'picab' } },
    })
    await screen.findAllByRole('radio')
    expect(
      screen.queryByRole('radio', { name: /Araport11/i }),
    ).not.toBeInTheDocument()
  })
})
