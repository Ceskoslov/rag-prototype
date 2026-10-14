/**
 * Dynamically discovered knowledge-base slug
 */
export type KnowledgeBase = string

/**
 * Retrieval source from agent trace
 */
export interface RetrievalSource {
  knowledge_base: string
  title: string
  snippet: string
  source_path?: string
  page?: number | null
  score?: number
}

/**
 * Agent trace information from backend
 */
export interface AgentTrace {
  knowledge_bases_searched: string[]
  retrieval_sources: RetrievalSource[]
  iterations: number
  pipeline_steps: string[]
  grounded?: boolean
  metrics?: { elapsed_ms?: number; first_token_ms?: number | null; tokens?: { total_tokens?: number }; stages?: Array<{ stage: string; duration_ms: number }> }
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
  knowledge_base?: KnowledgeBase
  agent_trace?: AgentTrace | null
}

/**
 * Request payload to chat endpoint
 */
export interface ChatRequest {
  message: string
  sessionId: string
  knowledge_base: KnowledgeBase | 'all'
}

/**
 * Response payload from chat endpoint
 */
export interface ChatResponse {
  message: ChatMessage
  session_id: string
  knowledge_bases: string[]
  suggestion_questions?: string[]
}
