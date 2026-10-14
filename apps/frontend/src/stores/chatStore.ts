import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import type { AgentTrace } from '@/types/chat'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: SourceDocument[]
  trace?: AgentTrace
}

export interface SourceDocument {
  title: string
  snippet: string
  knowledge_base: string
  citation_id?: number
  content?: string
  source_path?: string
  page?: number | null
}

interface ChatStore {
  messages: ChatMessage[]
  isLoading: boolean
  knowledgeBase: string
  sessionId: string
  agentTrace: AgentTrace | null
  sources: SourceDocument[]
  error: string | null
  stage: string
  verified: boolean
  setStage: (stage: string) => void
  setVerified: (verified: boolean) => void
  replaceLastMessage: (content: string) => void
  restoreSession: (sessionId: string, knowledgeBase: string, messages: ChatMessage[]) => void
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
        stage: "",
        verified: false,
        setStage: (stage) => set({ stage }),
        setVerified: (verified) => set({ verified }),
        replaceLastMessage: (content) => set((state) => ({ messages: state.messages.map((message, index) => index === state.messages.length - 1 ? { ...message, content } : message) })),
        restoreSession: (sessionId, knowledgeBase, messages) => set({ sessionId, knowledgeBase, messages, sources: messages.at(-1)?.sources || [], agentTrace: messages.at(-1)?.trace || null, error: null, stage: "", verified: Boolean(messages.at(-1)?.trace?.grounded) }),
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
        clearMessages: () => set({ messages: [], sessionId: crypto.randomUUID(), sources: [], agentTrace: null, error: null, stage: "", verified: false }),
        setAgentTrace: (trace) => set({ agentTrace: trace }),
        setSources: (sources) => set((state) => ({ sources, messages: state.messages.map((message, index) => index === state.messages.length - 1 && message.role === "assistant" ? { ...message, sources } : message) })),
        setError: (error) => set({ error }),
      }),
      {
        name: 'chat-store',
        partialize: (state) => ({ sessionId: state.sessionId }),
      }
    )
  )
)
