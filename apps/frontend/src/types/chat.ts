/**
 * Department enum matching backend Pydantic enum
 */
export type Department = 'it_support' | 'legal' | 'credit_card' | 'airport_ground'

/**
 * Agent trace information from backend
 */
export interface AgentTrace {
  agent_name: string
  reasoning: string
  action: string
  observation?: string
  timestamp: string
}

/**
 * Chat message structure
 */
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  department?: Department
  agent_trace?: AgentTrace | null
}

/**
 * Request payload to chat endpoint
 */
export interface ChatRequest {
  message: string
  sessionId: string
  department: Department | 'auto'
}

/**
 * Response payload from chat endpoint
 */
export interface ChatResponse {
  message: ChatMessage
  session_id: string
  suggestion_questions?: string[]
}
