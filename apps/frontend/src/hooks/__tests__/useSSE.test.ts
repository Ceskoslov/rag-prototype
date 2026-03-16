import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useSSE } from '../useSSE'

describe('useSSE', () => {
  let eventSourceMock: Partial<EventSource>
  let onOpenCallback: (() => void) | null = null
  let onMessageCallback: ((event: MessageEvent) => void) | null = null
  let onErrorCallback: ((error: Event) => void) | null = null

  beforeEach(() => {
    onOpenCallback = null
    onMessageCallback = null
    onErrorCallback = null

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

  describe('basic connection', () => {
    it('should initialize with disconnected state', () => {
      const { result } = renderHook(() => useSSE('http://localhost/stream'))
      expect(result.current.isConnected).toBe(false)
      expect(result.current.error).toBeNull()
    })

    it('should connect and call onopen', () => {
      const { result } = renderHook(() => useSSE('http://localhost/stream'))

      act(() => {
        result.current.connect()

        const es = eventSourceMock as any
        if (es.onopen) es.onopen()
      })

      expect(result.current.isConnected).toBe(true)
      expect(result.current.error).toBeNull()
    })

    it('should set error on connection error', () => {
      const { result } = renderHook(() => useSSE('http://localhost/stream'))

      act(() => {
        result.current.connect()

        const es = eventSourceMock as any
        if (es.onerror) es.onerror(new Event('error'))
      })

      expect(result.current.isConnected).toBe(false)
      expect(result.current.error).not.toBeNull()
    })

    it('should disconnect and close EventSource', () => {
      const { result } = renderHook(() => useSSE('http://localhost/stream'))

      act(() => {
        result.current.connect()
      })

      act(() => {
        result.current.disconnect()
      })

      expect(eventSourceMock.close).toHaveBeenCalled()
      expect(result.current.isConnected).toBe(false)
    })
  })

  describe('message handling', () => {
    it('should call onMessage callback with parsed JSON data', () => {
      const onMessage = vi.fn()
      const { result } = renderHook(() => useSSE('http://localhost/stream', { onMessage }))

      act(() => {
        result.current.connect()

        const es = eventSourceMock as any
        if (es.onopen) es.onopen()
      })

      const messageData = { type: 'token', content: 'Hello' }
      act(() => {
        const es = eventSourceMock as any
        if (es.onmessage) {
          es.onmessage(
            new MessageEvent('message', {
              data: JSON.stringify(messageData),
            })
          )
        }
      })

      expect(onMessage).toHaveBeenCalledWith(messageData)
    })

    it('should handle invalid JSON gracefully', () => {
      const onMessage = vi.fn()
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const { result } = renderHook(() => useSSE('http://localhost/stream', { onMessage }))

      act(() => {
        result.current.connect()

        const es = eventSourceMock as any
        if (es.onopen) es.onopen()
      })

      act(() => {
        const es = eventSourceMock as any
        if (es.onmessage) {
          es.onmessage(
            new MessageEvent('message', {
              data: 'invalid json {',
            })
          )
        }
      })

      expect(onMessage).not.toHaveBeenCalled()
      expect(consoleErrorSpy).toHaveBeenCalled()
      consoleErrorSpy.mockRestore()
    })
  })

  describe('error handling and reconnection', () => {
    it('should call onError callback on error', () => {
      const onError = vi.fn()
      const { result } = renderHook(() => useSSE('http://localhost/stream', { onError }))

      act(() => {
        result.current.connect()

        const es = eventSourceMock as any
        if (es.onerror) es.onerror(new Event('error'))
      })

      expect(onError).toHaveBeenCalled()
    })

    it('should not send empty URL', () => {
      const { result } = renderHook(() => useSSE(''))

      act(() => {
        result.current.connect()
      })

      expect(global.EventSource).not.toHaveBeenCalled()
    })
  })

  describe('cleanup', () => {
    it('should disconnect on unmount', () => {
      const { unmount, result } = renderHook(() => useSSE('http://localhost/stream'))

      act(() => {
        result.current.connect()
      })

      unmount()

      expect(eventSourceMock.close).toHaveBeenCalled()
    })
  })
})
