import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useChat } from '../useChat'
import { useChatStore } from '../../stores/chatStore'

describe('useChat', () => {
  let eventSourceMock: Partial<EventSource>

  beforeEach(() => {
    useChatStore.setState({
      messages: [],
      isLoading: false,
      department: 'auto',
      agentTrace: null,
    })

    eventSourceMock = {
      close: vi.fn(),
    }

    const EventSourceConstructor = vi.fn(function (url: string) {
      return eventSourceMock
    })

    Object.defineProperty(EventSourceConstructor, Symbol.hasInstance, {
      value: (obj: unknown) => obj === eventSourceMock,
    })

    vi.stubGlobal('EventSource', EventSourceConstructor)
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.unstubAllGlobals()
  })

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

    it('should create EventSource with correct URL', () => {
      const { result } = renderHook(() => useChat())

      act(() => {
        result.current.sendMessage('Hello')
      })

      expect(global.EventSource).toHaveBeenCalled()
      const callUrl = (global.EventSource as any).mock.calls[0][0] as string
      expect(callUrl).toContain('/chat/stream')
      expect(callUrl).toContain('message=Hello')
      expect(callUrl).toContain('session_id=')
    })

    it('should send specific department when selected', () => {
      const { result } = renderHook(() => useChat())

      act(() => {
        useChatStore.setState({ department: 'it_support' })
      })

      act(() => {
        result.current.sendMessage('Test')
      })

      const callUrl = (global.EventSource as any).mock.calls[0][0] as string
      expect(callUrl).toContain('department=it_support')
    })
  })

  describe('SSE message handling', () => {
    it('should append token to last assistant message', () => {
      const { result } = renderHook(() => useChat())

      act(() => {
        result.current.sendMessage('Hello')
      })

      act(() => {
        const es = eventSourceMock as any
        if (es.onmessage) {
          es.onmessage(
            new MessageEvent('message', {
              data: JSON.stringify({ type: 'token', content: 'Hi' }),
            })
          )
          es.onmessage(
            new MessageEvent('message', {
              data: JSON.stringify({ type: 'token', content: ' there' }),
            })
          )
        }
      })

      const store = useChatStore.getState()
      expect(store.messages[1].content).toBe('Hi there')
    })

    it('should set agent trace when received', () => {
      const { result } = renderHook(() => useChat())

      act(() => {
        result.current.sendMessage('Test')
      })

      const trace = { 
        supervisor_decision: 'Routing to Legal',
        agents_invoked: ['legal'], 
        retrieval_sources: [],
        iterations: 1,
        confidence: 0.85,
      }
      act(() => {
        const es = eventSourceMock as any
        if (es.onmessage) {
          es.onmessage(
            new MessageEvent('message', {
              data: JSON.stringify({ type: 'trace', ...trace }),
            })
          )
        }
      })

      const store = useChatStore.getState()
      expect(store.agentTrace).toEqual({ ...trace, type: 'trace' })
    })

    it('should set loading to false and close on done', () => {
      const { result } = renderHook(() => useChat())

      act(() => {
        result.current.sendMessage('Test')
      })

      act(() => {
        const es = eventSourceMock as any
        if (es.onmessage) {
          es.onmessage(
            new MessageEvent('message', {
              data: JSON.stringify({ type: 'done' }),
            })
          )
        }
      })

      const store = useChatStore.getState()
      expect(store.isLoading).toBe(false)
      expect(eventSourceMock.close).toHaveBeenCalled()
    })

    it('should ignore unknown message types', () => {
      const { result } = renderHook(() => useChat())

      act(() => {
        result.current.sendMessage('Test')
      })

      act(() => {
        const es = eventSourceMock as any
        if (es.onmessage) {
          es.onmessage(
            new MessageEvent('message', {
              data: JSON.stringify({ type: 'unknown', content: 'data' }),
            })
          )
        }
      })

      const store = useChatStore.getState()
      expect(store.isLoading).toBe(true)
    })
  })

  describe('error handling', () => {
    it('should handle connection error', () => {
      const { result } = renderHook(() => useChat())

      act(() => {
        result.current.sendMessage('Test')
      })

      act(() => {
        const es = eventSourceMock as any
        if (es.onerror) {
          es.onerror(new Event('error'))
        }
      })

      const store = useChatStore.getState()
      expect(store.isLoading).toBe(false)
      expect(eventSourceMock.close).toHaveBeenCalled()
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
