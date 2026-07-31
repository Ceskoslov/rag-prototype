import { useCallback } from 'react'
import { useChatStore } from '../stores/chatStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const API_KEY = import.meta.env.VITE_API_KEY || 'test-key'

export const useChat = () => {
  const {
    messages,
    isLoading,
    knowledgeBase,
    sessionId,
    agentTrace,
    sources,
    addMessage,
    updateLastMessage,
    setLoading,
    setKnowledgeBase,
    clearMessages,
    setAgentTrace,
    setSources,
    setError,
  } = useChatStore()

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return

    addMessage('user', text)
    setLoading(true)
    setAgentTrace(null)
    setSources([])
    setError(null)

    addMessage('assistant', '')

    const url = `${API_BASE_URL}/chat/stream`
    const payload = {
      message: text,
      session_id: sessionId,
      knowledge_base: knowledgeBase === 'all' ? null : knowledgeBase,
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Invalid API key. Please check your credentials.')
        }
        throw new Error(`API error: ${response.status} ${response.statusText}`)
      }

      if (!response.body) {
        throw new Error('No response body')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data: ')) continue

          const data = line.substring(6)
          try {
            const event = JSON.parse(data)

            if (event.type === 'token') {
              updateLastMessage(event.content)
            } else if (event.type === 'sources') {
              setSources(event.data || [])
            } else if (event.type === 'trace') {
              setAgentTrace(event.data)
            } else if (event.type === 'done') {
              setLoading(false)
            }
          } catch (err) {
            console.error('Failed to parse SSE event:', err, data)
          }
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Network error. Please try again.'
      setError(errorMessage)
      setLoading(false)
      console.error('Chat stream error:', err)
    }
  }, [isLoading, knowledgeBase, sessionId, addMessage, setLoading, setAgentTrace, updateLastMessage, setSources, setError])

  return {
    messages,
    isLoading,
    knowledgeBase,
    agentTrace,
    sources,
    sendMessage,
    setKnowledgeBase,
    clearMessages,
  }
}
