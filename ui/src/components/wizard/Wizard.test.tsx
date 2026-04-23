import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithStore } from '../../test-utils'
import Wizard from './Wizard'

describe('Wizard', () => {
  it('disables Continue on step 1 when name is empty', () => {
    renderWithStore(<Wizard />)
    expect(screen.getByRole('button', { name: /continue/i })).toBeDisabled()
  })

  it('enables Continue after typing a name', async () => {
    const user = userEvent.setup()
    renderWithStore(<Wizard />)
    await user.type(screen.getByLabelText(/list name/i), 'My list')
    expect(screen.getByRole('button', { name: /continue/i })).toBeEnabled()
  })

  it('advances to step 2 when Continue is clicked on step 1', async () => {
    const user = userEvent.setup()
    renderWithStore(<Wizard />, {
      preloadedState: {
        wizard: {
          step: 1,
          name: 'My list',
          description: '',
          taxonId: null,
          genomeId: null,
        },
      },
    })
    await user.click(screen.getByRole('button', { name: /continue/i }))
    expect(
      screen.getByRole('heading', { name: /select a taxon/i }),
    ).toBeInTheDocument()
    expect(screen.getAllByRole('radio')).toHaveLength(7)
  })

  it('Back on step 2 returns to step 1 with name preserved', async () => {
    const user = userEvent.setup()
    renderWithStore(<Wizard />, {
      preloadedState: {
        wizard: {
          step: 2,
          name: 'My list',
          description: '',
          taxonId: 'pinus-sylvestris',
          genomeId: null,
        },
      },
    })
    await user.click(screen.getByRole('button', { name: /back/i }))
    expect(
      screen.getByRole('heading', { name: /name your list/i }),
    ).toBeInTheDocument()
    expect(screen.getByLabelText(/list name/i)).toHaveValue('My list')
  })

  it('step 3 shows the selected taxon and a Create list button', () => {
    renderWithStore(<Wizard />, {
      preloadedState: {
        wizard: {
          step: 3,
          name: 'My list',
          description: '',
          taxonId: 'pinus-sylvestris',
          genomeId: null,
        },
      },
    })
    expect(
      screen.getByText(/new gene list.*pinus sylvestris/i),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /create list/i }),
    ).toBeInTheDocument()
  })

  it('step 2 Continue is disabled until a taxon is picked', async () => {
    const user = userEvent.setup()
    renderWithStore(<Wizard />, {
      preloadedState: {
        wizard: {
          step: 2,
          name: 'My list',
          description: '',
          taxonId: null,
          genomeId: null,
        },
      },
    })
    expect(screen.getByRole('button', { name: /continue/i })).toBeDisabled()
    await user.click(screen.getByRole('radio', { name: /pinus sylvestris/i }))
    expect(screen.getByRole('button', { name: /continue/i })).toBeEnabled()
  })
})
