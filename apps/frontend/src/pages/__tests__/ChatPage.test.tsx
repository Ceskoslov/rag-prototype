import { render, screen, waitFor } from '@testing-library/react'
import { useChatStore } from '@/stores/chatStore'
import { ChatPage } from '../ChatPage'

describe('ChatPage', () => {
  it('loads and displays dynamic knowledge bases', async () => {
    useChatStore.setState({
      messages: [],
      isLoading: false,
      knowledgeBase: 'all',
      agentTrace: null,
      sources: [],
      error: null,
    })
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url: string) => ({
        ok: true,
        json: async () => url.endsWith("/sessions") ? [] : [{ name: "product_docs" }, { name: "policies" }],
      })),
    )

    render(<ChatPage />)

    expect(screen.getByText('Universal RAG')).toBeInTheDocument()
    expect(screen.getByLabelText('Knowledge base')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('Product Docs')).toBeInTheDocument())
  })
})
