import { act } from '@testing-library/react'
import { useChatStore } from '../chatStore'

describe('useChatStore', () => {
  beforeEach(() => {
    useChatStore.setState({
      messages: [],
      isLoading: false,
      knowledgeBase: 'all',
      agentTrace: null,
      sources: [],
      error: null,
    })
  })

  it('selects arbitrary knowledge bases', () => {
    act(() => useChatStore.getState().setKnowledgeBase('product_docs'))
    expect(useChatStore.getState().knowledgeBase).toBe('product_docs')
  })

  it('appends streamed answer tokens', () => {
    act(() => {
      useChatStore.getState().addMessage('assistant', '')
      useChatStore.getState().updateLastMessage('Hello')
      useChatStore.getState().updateLastMessage(' world')
    })
    expect(useChatStore.getState().messages[0].content).toBe('Hello world')
  })
})


it('new chat starts a new server session and clears evidence', () => {
  const previous = useChatStore.getState().sessionId
  useChatStore.getState().clearMessages()
  expect(useChatStore.getState().sessionId).not.toBe(previous)
  expect(useChatStore.getState().sources).toEqual([])
})
