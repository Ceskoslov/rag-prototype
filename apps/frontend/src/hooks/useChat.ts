import { useCallback } from 'react'
import { useChatStore } from '../stores/chatStore'
import { useSSE } from './useSSE'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const useChat = () => {
  const {
    messages,
    isLoading,
    department,
    sessionId,
    agentTrace,
    addMessage,
    updateLastMessage,
    setLoading,
    setDepartment,
    clearMessages,
    setAgentTrace,
  } = useChatStore()

  const sendMessage = useCallback((text: string) => {
    if (!text.trim() || isLoading) return

    addMessage('user', text)
    setLoading(true)
    setAgentTrace(null)

    addMessage('assistant', '')

    const url = `${API_BASE_URL}/chat/stream`
    const params = new URLSearchParams({
      message: text,
      session_id: sessionId,
      department: department === 'auto' ? '' : department,
    })

    const eventSource = new EventSource(`${url}?${params}`)

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'token') {
        updateLastMessage(data.content)
      } else if (data.type === 'trace') {
        setAgentTrace(data)
      } else if (data.type === 'done') {
        setLoading(false)
        eventSource.close()
      }
    }

    eventSource.onerror = () => {
      setLoading(false)
      eventSource.close()
    }
  }, [isLoading, department, sessionId, addMessage, setLoading, setAgentTrace, updateLastMessage])

  return {
    messages,
    isLoading,
    department,
    agentTrace,
    sendMessage,
    setDepartment,
    clearMessages,
  }
}
