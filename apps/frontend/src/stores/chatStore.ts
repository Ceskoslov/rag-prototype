import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import type { Department, AgentTrace } from '@/types/chat'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export type DepartmentType = 'it_support' | 'legal' | 'credit_card' | 'airport_ground' | 'auto'

interface ChatStore {
  messages: ChatMessage[]
  isLoading: boolean
  department: DepartmentType
  sessionId: string
  agentTrace: AgentTrace | null
  addMessage: (role: 'user' | 'assistant', content: string) => void
  updateLastMessage: (content: string) => void
  setLoading: (loading: boolean) => void
  setDepartment: (dept: DepartmentType) => void
  clearMessages: () => void
  setAgentTrace: (trace: AgentTrace | null) => void
}

export const useChatStore = create<ChatStore>()(
  devtools(
    persist(
      (set) => ({
        messages: [],
        isLoading: false,
        department: 'auto',
        sessionId: crypto.randomUUID(),
        agentTrace: null,
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
        setDepartment: (dept) => set({ department: dept }),
        clearMessages: () => set({ messages: [] }),
        setAgentTrace: (trace) => set({ agentTrace: trace }),
      }),
      {
        name: 'chat-store',
        partialize: (state) => ({ sessionId: state.sessionId }),
      }
    )
  )
)
