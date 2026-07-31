import { fireEvent, render, screen } from '@testing-library/react'
import { KnowledgeBaseSelector } from '../KnowledgeBaseSelector'

describe('KnowledgeBaseSelector', () => {
  it('renders knowledge bases discovered by the API', () => {
    render(
      <KnowledgeBaseSelector
        value="all"
        options={['product_docs', 'policies']}
        onChange={vi.fn()}
      />,
    )
    expect(screen.getByText('All knowledge bases')).toBeInTheDocument()
    expect(screen.getByText('Product Docs')).toBeInTheDocument()
    expect(screen.getByText('Policies')).toBeInTheDocument()
  })

  it('reports selection changes', () => {
    const onChange = vi.fn()
    render(
      <KnowledgeBaseSelector
        value="all"
        options={['policies']}
        onChange={onChange}
      />,
    )
    fireEvent.change(screen.getByLabelText('Knowledge base'), {
      target: { value: 'policies' },
    })
    expect(onChange).toHaveBeenCalledWith('policies')
  })
})
