import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useChat } from '../useChat'
import { useChatStore } from '../../stores/chatStore'

describe('useChat', () => {
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    useChatStore.setState({
      messages: [],
      isLoading: false,
      department: 'auto',
      agentTrace: null,
      sources: [],
      error: null,
    })

    mockFetch = vi.fn()
    vi.stubGlobal('fetch', mockFetch)
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.unstubAllGlobals()
  })

  const createSSEResponse = (events: Array<{ type: string; content?: string; data?: any }>) => {
    const encoder = new TextEncoder()
    const chunks = events.map(event => {
      const payload = event.type === 'token' 
        ? { type: event.type, content: event.content }
        : { type: event.type, data: event.data }
      return encoder.encode(`data: ${JSON.stringify(payload)}\n\n`)
    })

    const stream = new ReadableStream({
      start(controller) {
        chunks.forEach(chunk => controller.enqueue(chunk))
        controller.close()
      }
    })

    return {
      ok: true,
      status: 200,
      body: stream,
    } as Response
  }

  describe('hook initialization', () => {
    it('should return initial state from store', () => {
      const { result } = renderHook(() => useChat())

      expect(result.current.messages).toEqual([])
      expect(result.current.isLoading).toBe(false)
      expect(result.current.department).toBe('auto')
      expect(result.current.agentTrace).toBeNull()
    })

    it('should have required functions', () => {
      const { result } = renderHook(() => useChat())

      expect(typeof result.current.sendMessage).toBe('function')
      expect(typeof result.current.setDepartment).toBe('function')
      expect(typeof result.current.clearMessages).toBe('function')
    })
  })

  describe('sendMessage', () => {
    it('should add user message and create empty assistant message', () => {
      const { result } = renderHook(() => useChat())

      act(() => {
        result.current.sendMessage('Hello')
      })

      const store = useChatStore.getState()
      expect(store.messages).toHaveLength(2)
      expect(store.messages[0]).toEqual({ role: 'user', content: 'Hello' })
      expect(store.messages[1]).toEqual({ role: 'assistant', content: '' })
    })

    it('should set loading state to true', () => {
      const { result } = renderHook(() => useChat())

      act(() => {
        result.current.sendMessage('Test')
      })

      const store = useChatStore.getState()
      expect(store.isLoading).toBe(true)
    })

    it('should clear agent trace', () => {
      const { result } = renderHook(() => useChat())
      const trace = { 
        supervisor_decision: 'Routing to IT Support',
        agents_invoked: ['it_support'], 
        retrieval_sources: [],
        iterations: 1,
        confidence: 0.9,
      }

      act(() => {
        useChatStore.setState({ agentTrace: trace })
      })

      act(() => {
        result.current.sendMessage('New message')
      })

      const store = useChatStore.getState()
      expect(store.agentTrace).toBeNull()
    })

    it('should not send empty message', () => {
      const { result } = renderHook(() => useChat())

      act(() => {
        result.current.sendMessage('   ')
      })

      const store = useChatStore.getState()
      expect(store.messages).toHaveLength(0)
    })

    it('should not send when already loading', () => {
      const { result } = renderHook(() => useChat())

      act(() => {
        useChatStore.setState({ isLoading: true })
      })

      act(() => {
        result.current.sendMessage('Test')
      })

      const store = useChatStore.getState()
      expect(store.messages).toHaveLength(0)
    })

    it('should call fetch with correct URL and headers', async () => {
      mockFetch.mockResolvedValue(createSSEResponse([{ type: 'done' }]))
      const { result } = renderHook(() => useChat())

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/chat/stream'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-API-Key': expect.any(String),
          }),
          body: expect.stringContaining('Hello'),
        })
      )
    })

    it('should send specific department when selected', async () => {
      mockFetch.mockResolvedValue(createSSEResponse([{ type: 'done' }]))
      const { result } = renderHook(() => useChat())

      act(() => {
        useChatStore.setState({ department: 'it_support' })
      })

      await act(async () => {
        await result.current.sendMessage('Test')
      })

      const callBody = JSON.parse(mockFetch.mock.calls[0][1].body)
      expect(callBody.department).toBe('it_support')
    })
  })

  describe('SSE message handling', () => {
    it('should append token to last assistant message', async () => {
      mockFetch.mockResolvedValue(createSSEResponse([
        { type: 'token', content: 'Hi' },
        { type: 'token', content: ' there' },
        { type: 'done' },
      ]))
      const { result } = renderHook(() => useChat())

      await act(async () => {
        await result.current.sendMessage('Hello')
      })

      await waitFor(() => {
        const store = useChatStore.getState()
        expect(store.messages[1].content).toBe('Hi there')
      })
    })

    it('should set agent trace when received', async () => {
      const trace = { 
        supervisor_decision: 'Routing to Legal',
        agents_invoked: ['legal'], 
        retrieval_sources: [],
        iterations: 1,
        confidence: 0.85,
      }
      mockFetch.mockResolvedValue(createSSEResponse([
        { type: 'trace', data: trace },
        { type: 'done' },
      ]))
      const { result } = renderHook(() => useChat())

      await act(async () => {
        await result.current.sendMessage('Test')
      })

      await waitFor(() => {
        const store = useChatStore.getState()
        expect(store.agentTrace).toEqual(trace)
      })
    })

    it('should set loading to false and close on done', async () => {
      mockFetch.mockResolvedValue(createSSEResponse([
        { type: 'done' },
      ]))
      const { result } = renderHook(() => useChat())

      await act(async () => {
        await result.current.sendMessage('Test')
      })

      await waitFor(() => {
        const store = useChatStore.getState()
        expect(store.isLoading).toBe(false)
      })
    })

    it('should ignore unknown message types', async () => {
      mockFetch.mockResolvedValue(createSSEResponse([
        { type: 'unknown', content: 'data' } as any,
        { type: 'done' },
      ]))
      const { result } = renderHook(() => useChat())

      await act(async () => {
        await result.current.sendMessage('Test')
      })

      await waitFor(() => {
        const store = useChatStore.getState()
        expect(store.isLoading).toBe(false)
      })
    })
  })

  describe('error handling', () => {
    it('should handle connection error', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))
      const { result } = renderHook(() => useChat())

      await act(async () => {
        await result.current.sendMessage('Test')
      })

      await waitFor(() => {
        const store = useChatStore.getState()
        expect(store.isLoading).toBe(false)
        expect(store.error).toBeTruthy()
      })
    })
  })

  describe('department selection', () => {
    it('should update department', () => {
      const { result } = renderHook(() => useChat())

      act(() => {
        result.current.setDepartment('legal')
      })

      const store = useChatStore.getState()
      expect(store.department).toBe('legal')
    })
  })

  describe('message clearing', () => {
    it('should clear all messages', () => {
      const { result } = renderHook(() => useChat())

      act(() => {
        result.current.sendMessage('Hello')
      })

      expect(useChatStore.getState().messages).toHaveLength(2)

      act(() => {
        result.current.clearMessages()
      })

      expect(useChatStore.getState().messages).toHaveLength(0)
    })
  })
})
