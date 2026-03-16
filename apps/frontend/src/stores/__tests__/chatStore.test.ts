import { describe, it, expect, beforeEach } from 'vitest'
import { useChatStore } from '../chatStore'

describe('useChatStore', () => {
  beforeEach(() => {
    useChatStore.setState({
      messages: [],
      isLoading: false,
      department: 'auto',
      agentTrace: null,
    })
  })

  describe('addMessage', () => {
    it('should add a user message', () => {
      const { addMessage } = useChatStore.getState()
      addMessage('user', 'Hello')
      expect(useChatStore.getState().messages).toHaveLength(1)
      expect(useChatStore.getState().messages[0]).toEqual({
        role: 'user',
        content: 'Hello',
      })
    })

    it('should add an assistant message', () => {
      const { addMessage } = useChatStore.getState()
      addMessage('assistant', 'Hi there')
      expect(useChatStore.getState().messages).toHaveLength(1)
      expect(useChatStore.getState().messages[0]).toEqual({
        role: 'assistant',
        content: 'Hi there',
      })
    })

    it('should append multiple messages', () => {
      const { addMessage } = useChatStore.getState()
      addMessage('user', 'Message 1')
      addMessage('assistant', 'Response 1')
      addMessage('user', 'Message 2')
      expect(useChatStore.getState().messages).toHaveLength(3)
    })
  })

  describe('updateLastMessage', () => {
    it('should append content to the last message', () => {
      const { addMessage, updateLastMessage } = useChatStore.getState()
      addMessage('assistant', 'Hello')
      updateLastMessage(' World')
      expect(useChatStore.getState().messages[0].content).toBe('Hello World')
    })

    it('should do nothing if messages are empty', () => {
      const { updateLastMessage } = useChatStore.getState()
      updateLastMessage('text')
      expect(useChatStore.getState().messages).toHaveLength(0)
    })

    it('should work for streaming multiple chunks', () => {
      const { addMessage, updateLastMessage } = useChatStore.getState()
      addMessage('assistant', '')
      updateLastMessage('Chunk')
      updateLastMessage(' 1')
      updateLastMessage(' and')
      updateLastMessage(' Chunk 2')
      expect(useChatStore.getState().messages[0].content).toBe('Chunk 1 and Chunk 2')
    })
  })

  describe('setLoading', () => {
    it('should set loading state to true', () => {
      useChatStore.getState().setLoading(true)
      expect(useChatStore.getState().isLoading).toBe(true)
    })

    it('should set loading state to false', () => {
      useChatStore.getState().setLoading(true)
      useChatStore.getState().setLoading(false)
      expect(useChatStore.getState().isLoading).toBe(false)
    })
  })

  describe('setDepartment', () => {
    it('should set department to it_support', () => {
      useChatStore.getState().setDepartment('it_support')
      expect(useChatStore.getState().department).toBe('it_support')
    })

    it('should set department to legal', () => {
      useChatStore.getState().setDepartment('legal')
      expect(useChatStore.getState().department).toBe('legal')
    })

    it('should set department to credit_card', () => {
      useChatStore.getState().setDepartment('credit_card')
      expect(useChatStore.getState().department).toBe('credit_card')
    })

    it('should set department to airport_ground', () => {
      useChatStore.getState().setDepartment('airport_ground')
      expect(useChatStore.getState().department).toBe('airport_ground')
    })

    it('should set department to auto', () => {
      useChatStore.getState().setDepartment('auto')
      expect(useChatStore.getState().department).toBe('auto')
    })
  })

  describe('clearMessages', () => {
    it('should clear all messages', () => {
      const { addMessage, clearMessages } = useChatStore.getState()
      addMessage('user', 'Message 1')
      addMessage('assistant', 'Response 1')
      expect(useChatStore.getState().messages).toHaveLength(2)
      clearMessages()
      expect(useChatStore.getState().messages).toHaveLength(0)
    })

    it('should be safe to clear when no messages exist', () => {
      useChatStore.getState().clearMessages()
      expect(useChatStore.getState().messages).toHaveLength(0)
    })
  })

  describe('setAgentTrace', () => {
    it('should set agent trace', () => {
      const trace = { 
        supervisor_decision: 'Routing to IT Support',
        agents_invoked: ['it_support'], 
        retrieval_sources: [],
        iterations: 1,
        confidence: 0.9,
      }
      useChatStore.getState().setAgentTrace(trace)
      expect(useChatStore.getState().agentTrace).toEqual(trace)
    })

    it('should clear agent trace by setting to null', () => {
      const trace = { 
        supervisor_decision: 'Routing to Legal',
        agents_invoked: ['legal'], 
        retrieval_sources: [],
        iterations: 1,
        confidence: 0.85,
      }
      useChatStore.getState().setAgentTrace(trace)
      useChatStore.getState().setAgentTrace(null)
      expect(useChatStore.getState().agentTrace).toBeNull()
    })
  })

  describe('sessionId', () => {
    it('should have a valid UUID sessionId', () => {
      const { sessionId } = useChatStore.getState()
      expect(typeof sessionId).toBe('string')
      expect(sessionId).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
    })

    it('should persist sessionId across store resets', () => {
      const initialSessionId = useChatStore.getState().sessionId
      useChatStore.setState({ messages: [] })
      const newSessionId = useChatStore.getState().sessionId
      expect(newSessionId).toBe(initialSessionId)
    })
  })
})
