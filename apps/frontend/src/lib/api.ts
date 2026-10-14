export const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const apiHeaders = (): Record<string, string> => {
  const key = import.meta.env.VITE_API_KEY
  return key ? { 'X-API-Key': key } : {}
}

export async function apiFetch(path: string, options: RequestInit = {}) {
  const headers = new Headers(apiHeaders())
  new Headers(options.headers).forEach((value, key) => headers.set(key, value))
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try { message = (await response.json()).detail || message } catch { /* Empty error body. */ }
    throw new Error(message)
  }
  return response
}
