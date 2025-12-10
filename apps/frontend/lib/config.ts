/**
 * Frontend Configuration
 * 
 * Centralized configuration for API endpoints and environment-specific settings.
 * Uses Next.js public environment variables that are embedded at build time.
 * 
 * DEPRECATED: Use `@/lib/api` for all new API calls.
 * This file is kept for backward compatibility during migration.
 */

import { getApiBaseUrl, apiFetch as robustApiFetch, apiUrl } from './api'

/**
 * API Base URL
 * 
 * @deprecated Use getApiBaseUrl() from '@/lib/api' instead
 */
export const API_BASE_URL = getApiBaseUrl()

/**
 * API Endpoints
 * 
 * All backend API endpoints, constructed from the base URL.
 * 
 * @deprecated Use apiUrl() from '@/lib/api' instead for dynamic URL construction
 */
export const API_ENDPOINTS = {
  // Airport autocomplete
  airports: apiUrl('/api/airports'),
  
  // Search endpoints
  searchFlights: apiUrl('/api/search/flights'),
  searchHotels: apiUrl('/api/search/hotels'),
  
  // Pricing endpoints
  pricingDateRange: apiUrl('/api/pricing/date-range'),
  pricingCacheStats: apiUrl('/api/pricing/cache-stats'),
  
  // Redirect endpoints
  redirect: apiUrl('/api/redirect'),
  redirectAviasales: apiUrl('/api/redirect/aviasales'),
  
  // Admin endpoints
  adminReconciliations: apiUrl('/api/admin/reconciliations'),
  
  // Health check
  health: apiUrl('/api/health'),
} as const

/**
 * Fetch with better error logging
 * 
 * @deprecated Use apiFetch() from '@/lib/api' instead
 * This now wraps the robust implementation with retry logic
 */
export async function apiFetch(url: string, options?: RequestInit): Promise<Response> {
  // If it's already a full URL, use it directly
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return robustApiFetch(url, options)
  }
  
  // Otherwise, treat it as a path
  return robustApiFetch(url, options)
}

/**
 * Development helper to log current configuration
 */
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  console.log('[Config] API Base URL:', API_BASE_URL)
  console.log('[Config] Environment:', process.env.NODE_ENV)
}
