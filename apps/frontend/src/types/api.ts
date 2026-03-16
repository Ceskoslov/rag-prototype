/**
 * Server-Sent Event structure from backend SSE stream
 */
export interface SSEEvent {
  type: 'message' | 'trace' | 'suggestion' | 'error' | 'done'
  data: unknown
  timestamp: string
}

/**
 * API error response
 */
export interface APIError {
  error: string
  details?: string
  code?: string
}
