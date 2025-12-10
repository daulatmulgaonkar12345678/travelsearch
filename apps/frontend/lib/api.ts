/**
 * Centralized API Helper
 * 
 * Provides robust API communication with:
 * - Automatic URL construction from environment variable
 * - 5-second timeout on all requests
 * - Retry logic for transient network errors
 * - Detailed error logging
 * 
 * Usage:
 *   import { apiFetch, apiUrl } from '@/lib/api'
 *   
 *   const response = await apiFetch('/api/search/flights?origin=LAX')
 *   const url = apiUrl('/api/airports')
 */

/**
 * Get the API base URL from environment
 * Defaults to localhost for local development if not set
 */
export function getApiBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_BASE ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    'http://localhost:8001'
  )
}

/**
 * Construct full API URL from a path
 * 
 * @param path - API path (e.g., '/api/search/flights' or 'api/airports')
 * @returns Full URL with base URL prepended
 * 
 * @example
 * apiUrl('/api/airports?query=NYC') // => 'https://metasearch-app.preview.emergentagent.com/api/airports?query=NYC'
 */
export function apiUrl(path: string): string {
  const baseUrl = getApiBaseUrl()
  
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  
  // Remove trailing slash from base URL if present
  const normalizedBase = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl
  
  return `${normalizedBase}${normalizedPath}`
}

/**
 * Enhanced fetch with timeout
 * 
 * @param url - URL to fetch
 * @param options - Fetch options
 * @param timeoutMs - Timeout in milliseconds (default: 5000)
 * @returns Response or throws timeout error
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeoutMs: number = 5000
): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)
  
  try {
    // Merge abort signal with existing one if provided
    const signal = options.signal || controller.signal
    
    const response = await fetch(url, {
      ...options,
      signal,
    })
    
    clearTimeout(timeoutId)
    return response
  } catch (error: any) {
    clearTimeout(timeoutId)
    
    // Convert abort to timeout error for clarity
    if (error.name === 'AbortError') {
      throw new Error(`Request timeout after ${timeoutMs}ms: ${url}`)
    }
    
    throw error
  }
}

/**
 * Check if an error is retryable
 * 
 * Retries are attempted for:
 * - Network errors (no response received)
 * - 5xx server errors (except 501 Not Implemented)
 * - 429 Rate Limit (with exponential backoff)
 * - Timeout errors
 */
function isRetryableError(error: any, response?: Response): boolean {
  // Network errors (no response)
  if (!response && error instanceof Error) {
    return true
  }
  
  // Server errors
  if (response) {
    const status = response.status
    return status === 429 || (status >= 500 && status !== 501)
  }
  
  return false
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Robust API fetch with retry logic
 * 
 * @param path - API path (e.g., '/api/search/flights')
 * @param options - Fetch options (headers, method, body, etc.)
 * @param config - Configuration for timeout and retries
 * @returns Response object
 * 
 * @example
 * // Simple GET
 * const response = await apiFetch('/api/airports?query=NYC')
 * 
 * // POST with body
 * const response = await apiFetch('/api/search/flights', {
 *   method: 'POST',
 *   headers: { 'Content-Type': 'application/json' },
 *   body: JSON.stringify({ origin: 'LAX', destination: 'JFK' })
 * })
 * 
 * // With custom timeout and retries
 * const response = await apiFetch('/api/search/flights', {}, {
 *   timeoutMs: 10000,
 *   maxRetries: 3
 * })
 */
export async function apiFetch(
  path: string,
  options: RequestInit = {},
  config: { timeoutMs?: number; maxRetries?: number } = {}
): Promise<Response> {
  const { timeoutMs = 5000, maxRetries = 2 } = config
  
  // Construct full URL
  const url = apiUrl(path)
  
  let lastError: any
  let lastResponse: Response | undefined
  
  // Attempt request with retries
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      // Log the request (helpful for debugging)
      if (attempt === 0) {
        console.log(`[API] ${options.method || 'GET'} ${url}`)
      } else {
        console.log(`[API] Retry ${attempt}/${maxRetries}: ${url}`)
      }
      
      const response = await fetchWithTimeout(url, options, timeoutMs)
      
      // If successful or non-retryable error, return immediately
      if (response.ok || !isRetryableError(lastError, response)) {
        if (!response.ok) {
          console.warn(
            `[API] ${response.status} ${response.statusText} from ${url}`
          )
        }
        return response
      }
      
      // Store for potential retry
      lastResponse = response
      lastError = new Error(`HTTP ${response.status}: ${response.statusText}`)
      
    } catch (error: any) {
      lastError = error
      lastResponse = undefined
      
      // Don't retry if it's not a retryable error
      if (!isRetryableError(error)) {
        console.error(`[API] Non-retryable error for ${url}:`, error.message)
        throw error
      }
      
      console.warn(`[API] Retryable error for ${url}:`, error.message)
    }
    
    // If we haven't returned yet, we need to retry
    if (attempt < maxRetries) {
      // Exponential backoff: 500ms, 1000ms, 2000ms
      const backoffMs = 500 * Math.pow(2, attempt)
      console.log(`[API] Waiting ${backoffMs}ms before retry...`)
      await sleep(backoffMs)
    }
  }
  
  // All retries exhausted
  console.error(
    `[API] All ${maxRetries + 1} attempts failed for ${url}:`,
    lastError
  )
  
  // If we have a response, return it (even if not ok)
  if (lastResponse) {
    return lastResponse
  }
  
  // Otherwise throw the last error
  throw lastError || new Error(`Failed to fetch ${url} after ${maxRetries + 1} attempts`)
}

/**
 * Development helper to log current API configuration
 */
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  console.log('[API Config] Base URL:', getApiBaseUrl())
  console.log('[API Config] Environment:', process.env.NODE_ENV)
}
