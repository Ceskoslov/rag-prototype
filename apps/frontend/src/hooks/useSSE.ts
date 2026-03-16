import { useState, useEffect, useCallback, useRef } from 'react'

export interface SSEOptions {
  onMessage?: (data: unknown) => void
  onError?: (error: Error) => void
}

export const useSSE = (url: string, options: SSEOptions = {}) => {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const reconnectDelayRef = useRef(1000) // Start with 1s

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    setIsConnected(false)
  }, [])

  const connect = useCallback(() => {
    if (!url) return

    disconnect()

    const es = new EventSource(url)
    eventSourceRef.current = es

    es.onopen = () => {
      setIsConnected(true)
      setError(null)
      reconnectDelayRef.current = 1000 // Reset backoff
    }

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        options.onMessage?.(data)
      } catch (err) {
        console.error('Failed to parse SSE message:', err)
      }
    }

    es.onerror = () => {
      const error = new Error('SSE connection error')
      setError(error)
      setIsConnected(false)
      options.onError?.(error)

      // Auto-reconnect with exponential backoff
      disconnect()
      reconnectTimeoutRef.current = window.setTimeout(() => {
        reconnectDelayRef.current = Math.min(reconnectDelayRef.current * 2, 30000)
        connect()
      }, reconnectDelayRef.current)
    }
  }, [url, options, disconnect])

  useEffect(() => {
    return () => {
      disconnect()
    }
  }, [disconnect])

  return { isConnected, error, connect, disconnect }
}
