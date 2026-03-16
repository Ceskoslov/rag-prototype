import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { LoadingIndicator } from '../LoadingIndicator'

describe('LoadingIndicator', () => {
  it('renders without crashing', () => {
    render(<LoadingIndicator />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('has aria-label for screen readers', () => {
    render(<LoadingIndicator />)
    expect(screen.getByLabelText('Loading')).toBeInTheDocument()
  })
})
