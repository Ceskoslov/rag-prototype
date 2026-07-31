import { render, screen } from '@testing-library/react'
import { SourceCard } from '../SourceCard'

describe('SourceCard', () => {
  it('renders a dynamic knowledge-base badge', () => {
    render(
      <SourceCard
        title="refunds.md"
        snippet="Refunds are available for 30 days."
        knowledgeBase="policies"
      />,
    )
    expect(screen.getByText('refunds.md')).toBeInTheDocument()
    expect(screen.getByText('policies')).toBeInTheDocument()
  })
})
