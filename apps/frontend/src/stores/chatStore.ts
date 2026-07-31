import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import type { AgentTrace } from '@/types/chat'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface SourceDocument {
  title: string
  snippet: string
  knowledge_base: string
}

interface ChatStore {
  messages: ChatMessage[]
  isLoading: boolean
  knowledgeBase: string
  sessionId: string
  agentTrace: AgentTrace | null
  sources: SourceDocument[]
  error: string | null
  addMessage: (role: 'user' | 'assistant', content: string) => void
  updateLastMessage: (content: string) => void
  setLoading: (loading: boolean) => void
  setKnowledgeBase: (knowledgeBase: string) => void
  clearMessages: () => void
  setAgentTrace: (trace: AgentTrace | null) => void
  setSources: (sources: SourceDocument[]) => void
  setError: (error: string | null) => void
}

export const useChatStore = create<ChatStore>()(
  devtools(
    persist(
      (set) => ({
        messages: [],
        isLoading: false,
        knowledgeBase: 'all',
        sessionId: crypto.randomUUID(),
        agentTrace: null,
        sources: [],
        error: null,
        addMessage: (role, content) =>
          set((state) => ({
            messages: [...state.messages, { role, content }],
          })),
        updateLastMessage: (content) =>
          set((state) => {
            const messages = [...state.messages]
            if (messages.length > 0) {
              messages[messages.length - 1].content += content
            }
            return { messages }
          }),
        setLoading: (loading) => set({ isLoading: loading }),
        setKnowledgeBase: (knowledgeBase) => set({ knowledgeBase }),
        clearMessages: () => set({ messages: [] }),
        setAgentTrace: (trace) => set({ agentTrace: trace }),
        setSources: (sources) => set({ sources }),
        setError: (error) => set({ error }),
      }),
      {
        name: 'chat-store',
        partialize: (state) => ({ sessionId: state.sessionId }),
      }
    )
  )
)
