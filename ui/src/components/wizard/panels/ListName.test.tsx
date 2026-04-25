import { describe, it, expect } from 'vitest'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithStore } from '../../../test-utils'
import ListName from './ListName'

describe('ListName', () => {
  it('renders the list name input with the Figma placeholder', () => {
    renderWithStore(<ListName />)
    const input = screen.getByLabelText(/list name/i)
    expect(input).toHaveAttribute(
      'placeholder',
      'e.g. Drought-response TFs in Pinus sylvestris',
    )
  })

  it('renders the description textarea', () => {
    renderWithStore(<ListName />)
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument()
  })

  it('reflects initial store state in the inputs', () => {
    renderWithStore(<ListName />, {
      preloadedState: {
        wizard: {
          step: 1,
          name: 'Existing list',
          description: 'Already typed',
          taxonId: null,
          annotationId: null,
        },
      },
    })
    expect(screen.getByLabelText(/list name/i)).toHaveValue('Existing list')
    expect(screen.getByLabelText(/description/i)).toHaveValue('Already typed')
  })

  it('typing in list name updates the store', async () => {
    const user = userEvent.setup()
    const { store } = renderWithStore(<ListName />)
    await user.type(screen.getByLabelText(/list name/i), 'My list')
    expect(store.getState().wizard.name).toBe('My list')
  })

  it('typing in description updates the store', async () => {
    const user = userEvent.setup()
    const { store } = renderWithStore(<ListName />)
    await user.type(
      screen.getByLabelText(/description/i),
      'Notes about the list',
    )
    expect(store.getState().wizard.description).toBe('Notes about the list')
  })
})
