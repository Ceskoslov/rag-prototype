import { useCallback, useEffect, useRef } from 'react'
import { useChatStore } from '../stores/chatStore'
import { apiFetch } from '@/lib/api'

export const useChat = () => {
  const state = useChatStore()
  const controllerRef = useRef<AbortController | null>(null)
  useEffect(() => () => controllerRef.current?.abort(), [])

  const cancel = useCallback(() => controllerRef.current?.abort(), [])
  const sendMessage = useCallback(async (text: string) => {
    const store = useChatStore.getState()
    if (!text.trim() || store.isLoading) return
    const controller = new AbortController()
    controllerRef.current = controller
    store.addMessage('user', text)
    store.addMessage('assistant', '')
    store.setLoading(true)
    store.setAgentTrace(null)
    store.setSources([])
    store.setError(null)
    store.setStage('Preparing answer')
    store.setVerified(false)
    let reader: ReadableStreamDefaultReader<Uint8Array> | undefined
    let completed = false
    try {
      const response = await apiFetch('/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({ message: text, session_id: store.sessionId, knowledge_base: store.knowledgeBase === 'all' ? null : store.knowledgeBase }),
      })
      if (!response.body) throw new Error('No response stream')
      reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      const handle = (frame: string) => {
        const payload = frame.split('\n').filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n')
        if (!payload) return
        const event = JSON.parse(payload)
        if (event.type === 'token') store.updateLastMessage(event.content)
        else if (event.type === 'reset') { store.replaceLastMessage(event.content || ''); store.setVerified(false) }
        else if (event.type === 'sources') store.setSources(event.data || [])
        else if (event.type === 'trace') store.setAgentTrace(event.data)
        else if (event.type === 'progress') store.setStage(event.data?.stage || 'Working')
        else if (event.type === 'verification') store.setVerified(Boolean(event.data?.grounded))
        else if (event.type === 'error') throw new Error(event.data?.message || 'Answer failed')
        else if (event.type === 'done') { completed = true; store.setVerified(Boolean(event.data?.grounded)) }
      }
      while (!completed) {
        const { done, value } = await reader.read()
        buffer += done ? decoder.decode() : decoder.decode(value, { stream: true })
        buffer = buffer.replace(/\r\n/g, '\n')
        let boundary: number
        while ((boundary = buffer.indexOf('\n\n')) >= 0) {
          handle(buffer.slice(0, boundary))
          buffer = buffer.slice(boundary + 2)
        }
        if (done) {
          if (buffer.trim()) handle(buffer)
          break
        }
      }
      if (!completed) throw new Error('Connection ended before the answer completed. Please retry.')
    } catch (error) {
      if (!controller.signal.aborted) store.setError(error instanceof Error ? error.message : 'Network error')
      else store.setStage('Cancelled')
    } finally {
      await reader?.cancel().catch(() => {})
      controllerRef.current = null
      store.setLoading(false)
      if (completed) store.setStage('')
    }
  }, [])
  return { ...state, sendMessage, cancel }
}
