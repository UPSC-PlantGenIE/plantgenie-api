import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { server } from '../../../mocks/server'
import { renderWithStore } from '../../../test-utils'
import TaxonSelector from './TaxonSelector'

const step2State = {
  step: 2 as const,
  name: '',
  description: '',
  taxonId: null,
  annotationId: null,
}

describe('TaxonSelector', () => {
  it('shows loading skeleton while taxa are being fetched', () => {
    renderWithStore(<TaxonSelector />, {
      preloadedState: { wizard: step2State },
    })
    expect(screen.getByText(/loading taxa/i)).toBeInTheDocument()
  })

  it('renders taxa returned from the API', async () => {
    renderWithStore(<TaxonSelector />, {
      preloadedState: { wizard: step2State },
    })
    const radios = await screen.findAllByRole('radio')
    expect(radios).toHaveLength(2)
  })

  it('marks the stored taxonId as checked', async () => {
    renderWithStore(<TaxonSelector />, {
      preloadedState: { wizard: { ...step2State, taxonId: 'pinsy' } },
    })
    expect(
      await screen.findByRole('radio', { name: /pinus sylvestris/i }),
    ).toBeChecked()
  })

  it('clicking a radio dispatches setTaxonId with the abbreviation', async () => {
    const user = userEvent.setup()
    const { store } = renderWithStore(<TaxonSelector />, {
      preloadedState: { wizard: step2State },
    })
    await user.click(
      await screen.findByRole('radio', { name: /picea abies/i }),
    )
    expect(store.getState().wizard.taxonId).toBe('picab')
  })

  it('changing taxon clears any existing annotationId', async () => {
    const user = userEvent.setup()
    const { store } = renderWithStore(<TaxonSelector />, {
      preloadedState: {
        wizard: {
          ...step2State,
          taxonId: 'pinsy',
          annotationId: 'pinsy-Araport11',
        },
      },
    })
    await user.click(
      await screen.findByRole('radio', { name: /picea abies/i }),
    )
    expect(store.getState().wizard.annotationId).toBeNull()
  })

  it('re-selecting the same taxon preserves annotationId', async () => {
    const user = userEvent.setup()
    const { store } = renderWithStore(<TaxonSelector />, {
      preloadedState: {
        wizard: {
          ...step2State,
          taxonId: 'pinsy',
          annotationId: 'pinsy-Araport11',
        },
      },
    })
    await user.click(
      await screen.findByRole('radio', { name: /pinus sylvestris/i }),
    )
    expect(store.getState().wizard.annotationId).toBe('pinsy-Araport11')
  })

  it('shows an error message when the request fails', async () => {
    server.use(
      http.get('http://localhost:8000/api/v2/taxa', () =>
        HttpResponse.error(),
      ),
    )
    renderWithStore(<TaxonSelector />, {
      preloadedState: { wizard: step2State },
    })
    expect(await screen.findByRole('alert')).toHaveTextContent(
      /couldn't load taxa/i,
    )
  })
})
