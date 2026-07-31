import { render, screen } from '@testing-library/react'
import { AgentTracePanel } from '../AgentTracePanel'

describe('AgentTracePanel', () => {
  it('shows generic knowledge bases, pipeline steps, and sources', () => {
    render(
      <AgentTracePanel
        trace={{
          knowledge_bases_searched: ['product_docs', 'policies'],
          pipeline_steps: ['retrieve', 'generate', 'critique'],
          retrieval_sources: [
            {
              title: 'refunds.md',
              snippet: 'Refunds are available for 30 days.',
              knowledge_base: 'policies',
            },
          ],
          iterations: 1,
          confidence: 0.9,
        }}
      />,
    )

    expect(screen.getByText('RAG trace')).toBeInTheDocument()
    expect(screen.getByText('Product Docs')).toBeInTheDocument()
    expect(screen.getAllByText('Policies')).toHaveLength(2)
    expect(screen.getByText('refunds.md')).toBeInTheDocument()
    expect(screen.getByText('retrieve → generate → critique')).toBeInTheDocument()
  })

  it('renders nothing without a trace', () => {
    const { container } = render(<AgentTracePanel trace={null} />)
    expect(container.firstChild).toBeNull()
  })
})
