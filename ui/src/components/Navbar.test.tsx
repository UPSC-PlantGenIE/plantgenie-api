import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Navbar from './Navbar'

describe('Navbar', () => {
  it('renders the GeneList wordmark', () => {
    render(<Navbar />)
    expect(screen.getByText('🌿 GeneList')).toBeInTheDocument()
  })

  it('exposes a banner landmark', () => {
    render(<Navbar />)
    expect(screen.getByRole('banner')).toBeInTheDocument()
  })
})
