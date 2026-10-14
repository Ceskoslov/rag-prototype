import { act, renderHook, waitFor } from '@testing-library/react'
import { useChatStore } from '@/stores/chatStore'
import { useChat } from '../useChat'

describe('useChat', () => {
  beforeEach(() => {
    useChatStore.setState({
      messages: [],
      isLoading: false,
      knowledgeBase: 'product_docs',
      agentTrace: null,
      sources: [],
      error: null,
    })
  })

  it('sends the selected knowledge base', async () => {
    const encoder = new TextEncoder()
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      body: new ReadableStream({
        start(controller) {
          controller.enqueue(
            encoder.encode(
              'data: {"type":"token","content":"Answer"}\n\ndata: {"type":"done"}\n\n',
            ),
          )
          controller.close()
        },
      }),
    })
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useChat())

    await act(async () => result.current.sendMessage('Question'))
    await waitFor(() => expect(useChatStore.getState().isLoading).toBe(false))

    const body = JSON.parse(fetchMock.mock.calls[0][1].body)
    expect(body.knowledge_base).toBe('product_docs')
    expect(useChatStore.getState().messages.at(-1)?.content).toBe('Answer')
  })
})


describe('stream failures', () => {
  beforeEach(() => useChatStore.setState({ messages: [], isLoading: false, error: null }))
  const responseFor = (frames: string) => ({ ok: true, body: new ReadableStream({ start(controller) { controller.enqueue(new TextEncoder().encode(frames)); controller.close() } }) })

  it('handles server error events and releases loading state', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(responseFor('data: {"type":"error","data":{"message":"Provider unavailable"}}\n\n')))
    const { result } = renderHook(() => useChat())
    await act(async () => result.current.sendMessage('Question'))
    expect(useChatStore.getState().error).toBe('Provider unavailable')
    expect(useChatStore.getState().isLoading).toBe(false)
  })

  it('reports a stream that closes without done', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(responseFor('data: {"type":"token","content":"Draft"}\n\n')))
    const { result } = renderHook(() => useChat())
    await act(async () => result.current.sendMessage('Question'))
    expect(useChatStore.getState().error).toMatch('Connection ended')
    expect(useChatStore.getState().isLoading).toBe(false)
  })

  it('replaces rejected drafts rather than appending them', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(responseFor('data: {"type":"token","content":"Bad draft"}\n\ndata: {"type":"reset","content":"Evidence insufficient"}\n\ndata: {"type":"done"}\n\n')))
    const { result } = renderHook(() => useChat())
    await act(async () => result.current.sendMessage('Question'))
    expect(useChatStore.getState().messages.at(-1)?.content).toBe('Evidence insufficient')
  })
})
