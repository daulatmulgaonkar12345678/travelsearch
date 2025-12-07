/**
 * Frontend Configuration
 * 
 * Centralized configuration for API endpoints and environment-specific settings.
 * Uses Next.js public environment variables that are embedded at build time.
 */

/**
 * API Base URL
 * 
 * For Emergent preview: Uses the preview domain
 * For local development: Falls back to http://localhost:8001
 * 
 * Set via NEXT_PUBLIC_API_BASE_URL environment variable in:
 * - .env.local (local development)
 * - .env.production (production build)
 * - Build environment (Emergent deployment)
 */
export const API_BASE_URL = 
  process.env.NEXT_PUBLIC_API_BASE_URL || 
  process.env.NEXT_PUBLIC_API_URL || // Legacy support
  'http://localhost:8001';

/**
 * API Endpoints
 * 
 * All backend API endpoints, constructed from the base URL.
 */
export const API_ENDPOINTS = {
  // Airport autocomplete
  airports: `${API_BASE_URL}/api/airports`,
  
  // Search endpoints
  searchFlights: `${API_BASE_URL}/api/search/flights`,
  searchHotels: `${API_BASE_URL}/api/search/hotels`,
  
  // Pricing endpoints
  pricingDateRange: `${API_BASE_URL}/api/pricing/date-range`,
  pricingCacheStats: `${API_BASE_URL}/api/pricing/cache-stats`,
  
  // Redirect endpoints
  redirect: `${API_BASE_URL}/api/redirect`,
  redirectAviasales: `${API_BASE_URL}/api/redirect/aviasales`,
  
  // Admin endpoints
  adminReconciliations: `${API_BASE_URL}/api/admin/reconciliations`,
  
  // Health check
  health: `${API_BASE_URL}/api/health`,
} as const;

/**
 * Fetch with better error logging
 * 
 * Wrapper around fetch that logs the URL and error details for debugging.
 */
export async function apiFetch(url: string, options?: RequestInit): Promise<Response> {
  try {
    console.log(`[API] Fetching: ${url}`);
    const response = await fetch(url, options);
    
    if (!response.ok) {
      console.error(`[API] Error ${response.status} from ${url}:`, response.statusText);
    }
    
    return response;
  } catch (error) {
    console.error(`[API] Failed to fetch ${url}:`, error);
    throw error;
  }
}

/**
 * Development helper to log current configuration
 */
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  console.log('[Config] API Base URL:', API_BASE_URL);
  console.log('[Config] Environment:', process.env.NODE_ENV);
}
