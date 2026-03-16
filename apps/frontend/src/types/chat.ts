/**
 * Department enum matching backend Pydantic enum
 */
export type Department = 'it_support' | 'legal' | 'credit_card' | 'airport_ground'

/**
 * Retrieval source from agent trace
 */
export interface RetrievalSource {
  department: Department
  title: string
  score: number
  content: string
}

/**
 * Agent trace information from backend
 */
export interface AgentTrace {
  supervisor_decision: string
  agents_invoked: string[]
  retrieval_sources: RetrievalSource[]
  iterations: number
  confidence?: number
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
