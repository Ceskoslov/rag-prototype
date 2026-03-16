import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import type { ChatMessage, Department, AgentTrace } from '@/types/chat'

interface ChatStore {
  messages: ChatMessage[]
  isLoading: boolean
  department: Department | 'auto'
  sessionId: string
  agentTrace: AgentTrace | null
  addMessage: (message: ChatMessage) => void
  setLoading: (loading: boolean) => void
  setDepartment: (dept: Department | 'auto') => void
  setSessionId: (id: string) => void
  setAgentTrace: (trace: AgentTrace | null) => void
  clearMessages: () => void
}

export const useChatStore = create<ChatStore>()(
  devtools(
    persist(
      (set) => ({
        messages: [],
        isLoading: false,
        department: 'auto',
        sessionId: '',
        agentTrace: null,
        addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
        setLoading: (loading) => set({ isLoading: loading }),
        setDepartment: (dept) => set({ department: dept }),
        setSessionId: (id) => set({ sessionId: id }),
        setAgentTrace: (trace) => set({ agentTrace: trace }),
        clearMessages: () => set({ messages: [] }),
      }),
      {
        name: 'chat-store',
        partialize: (state) => ({ sessionId: state.sessionId }),
      }
    ),
    { name: 'ChatStore' }
  )
)
