/**
 * Centralized API Configuration
 * 
 * Single source of truth for API base URL across the application.
 * 
 * Usage:
 * - Import { getApiBase, apiFetch, apiUrl } from '@/lib/api'
 * - Use apiFetch('/api/search/flights', options) for all API calls
 * 
 * Environment:
 * - Local: Empty NEXT_PUBLIC_API_BASE uses Next.js rewrites (localhost:8001)
 * - Production: NEXT_PUBLIC_API_BASE = https://travelsearch-backend.onrender.com
 */

/**
 * Get the API base URL
 * - Returns empty string for local development (uses Next.js rewrites)
 * - Returns production URL in deployed environment
 */
export function getApiBase(): string {
  return process.env.NEXT_PUBLIC_API_BASE || ''
}

// Alias for backward compatibility
export const getApiBaseUrl = getApiBase

/**
 * Build a full API URL
 */
export function buildApiUrl(path: string): string {
  const base = getApiBase()
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${base}${normalizedPath}`
}

// Alias for backward compatibility
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
export async function apiGet<T = any>(path: string): Promise<T> {
  const response = await apiFetch(path)
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `API Error: ${response.status}`)
  }
  
  return response.json()
}

/**
 * Autocomplete-specific fetch with timeout and fallback
 */
export async function autocompleteSearch<T = any>(
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
  
  const url = buildApiUrl(`${endpoint}?${params.toString()}`)
  
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
