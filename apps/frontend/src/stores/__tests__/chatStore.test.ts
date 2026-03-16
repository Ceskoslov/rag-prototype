import { describe, it, expect, beforeEach } from 'vitest'
import { useChatStore } from '../chatStore'

describe('chatStore', () => {
  beforeEach(() => {
    useChatStore.getState().clearMessages()
  })

  it('should have initial state', () => {
    const store = useChatStore.getState()
    expect(store.messages).toEqual([])
    expect(store.isLoading).toBe(false)
    expect(store.department).toBe('auto')
    expect(store.sessionId).toBe('')
    expect(store.agentTrace).toBeNull()
  })

  it('should add a message', () => {
    const store = useChatStore.getState()
    const message = {
      id: '1',
      role: 'user' as const,
      content: 'Hello',
      timestamp: new Date().toISOString(),
    }

    store.addMessage(message)

    const updatedStore = useChatStore.getState()
    expect(updatedStore.messages).toHaveLength(1)
    expect(updatedStore.messages[0]).toEqual(message)
  })

  it('should set loading state', () => {
    const store = useChatStore.getState()
    store.setLoading(true)

    let updatedStore = useChatStore.getState()
    expect(updatedStore.isLoading).toBe(true)

    store.setLoading(false)
    updatedStore = useChatStore.getState()
    expect(updatedStore.isLoading).toBe(false)
  })

  it('should set department', () => {
    const store = useChatStore.getState()
    store.setDepartment('it_support')

    const updatedStore = useChatStore.getState()
    expect(updatedStore.department).toBe('it_support')
  })

  it('should set session id', () => {
    const store = useChatStore.getState()
    store.setSessionId('session-123')

    const updatedStore = useChatStore.getState()
    expect(updatedStore.sessionId).toBe('session-123')
  })

  it('should clear messages', () => {
    const store = useChatStore.getState()
    store.addMessage({
      id: '1',
      role: 'user',
      content: 'Test',
      timestamp: new Date().toISOString(),
    })

    let updatedStore = useChatStore.getState()
    expect(updatedStore.messages).toHaveLength(1)

    store.clearMessages()
    updatedStore = useChatStore.getState()
    expect(updatedStore.messages).toHaveLength(0)
  })
})
