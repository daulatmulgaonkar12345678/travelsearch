/**
 * Centralized API Configuration
 * 
 * ARCHITECTURE RULE (MANDATORY):
 * - Browser MUST NEVER call backend directly
 * - All API calls use relative URLs (/api/...)
 * - Next.js API routes proxy to backend
 * 
 * This ensures:
 * - No CORS errors
 * - Works on localhost, Vercel preview, production
 * - No environment-specific failures
 * 
 * Usage:
 * - Import { apiFetch } from '@/lib/api'
 * - Use apiFetch('/api/search/flights', options) for all API calls
 */

/**
 * Build API URL - ALWAYS returns relative path
 * Browser calls /api/* which Next.js proxies to backend
 */
export function buildApiUrl(path: string): string {
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  // ALWAYS return relative URL - never prepend external domain
  return normalizedPath
}

// Backward compatibility aliases
export const getApiBase = () => ''
export const getApiBaseUrl = getApiBase
export const apiUrl = buildApiUrl

/**
 * Raw fetch wrapper that returns Response object
 * Use this when you need to check response.ok or handle errors manually
 */
export async function apiFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const url = buildApiUrl(path)
  
  const defaultHeaders: HeadersInit = {
    'Accept': 'application/json',
  }
  
  // Only add Content-Type for non-GET requests with body
  if (options.body) {
    (defaultHeaders as Record<string, string>)['Content-Type'] = 'application/json'
  }
  
  return fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  })
}

/**
 * Type-safe fetch that parses JSON and throws on error
 * Use this for simple cases where you just want the data
 */
export async function apiGet<T = unknown>(path: string): Promise<T> {
  const response = await apiFetch(path)
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `API Error: ${response.status}`)
  }
  
  return response.json()
}

/**
 * Autocomplete-specific fetch with timeout
 */
export async function autocompleteSearch<T = unknown>(
  endpoint: string,
  query: string,
  options: {
    limit?: number
    mode?: string
    timeout?: number
  } = {}
): Promise<T[]> {
  const { limit = 15, mode, timeout = 5000 } = options
  
  if (!query || query.length < 2) {
    return []
  }
  
  const params = new URLSearchParams({ q: query, limit: String(limit) })
  if (mode) params.set('mode', mode)
  
  // Always use relative URL
  const url = `${endpoint}?${params.toString()}`
  
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeout)
    
    const response = await fetch(url, {
      headers: { 'Accept': 'application/json' },
      signal: controller.signal,
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      console.warn(`Autocomplete API returned ${response.status}`)
      return []
    }
    
    const data = await response.json()
    
    // Handle different response formats
    if (Array.isArray(data)) {
      return data
    }
    if (data.results && Array.isArray(data.results)) {
      return data.results
    }
    
    return []
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      console.warn('Autocomplete request timed out')
    } else {
      console.error('Autocomplete fetch error:', error)
    }
    return []
  }
}
