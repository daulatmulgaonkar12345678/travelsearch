/**
 * Environment Configuration & Validation
 * =======================================
 * 
 * PRODUCTION RULES:
 * - BACKEND_URL MUST be set
 * - No fallback data allowed
 * - Fail fast on misconfiguration
 */

export const ENV = {
  isProduction: process.env.NODE_ENV === 'production',
  isPreview: process.env.VERCEL_ENV === 'preview',
  isDevelopment: process.env.NODE_ENV === 'development',
  backendUrl: process.env.BACKEND_URL,
} as const

/**
 * Get backend URL with environment validation.
 * In production: MUST have BACKEND_URL, throws if missing.
 * In development/preview: Falls back to localhost.
 */
export function getBackendUrl(): string {
  if (ENV.backendUrl) {
    return ENV.backendUrl
  }

  if (ENV.isProduction) {
    throw new Error(
      '[FATAL] BACKEND_URL environment variable is not set in production. ' +
      'Set BACKEND_URL=https://travelsearch-backend.onrender.com in Vercel environment variables.'
    )
  }

  // Development/preview fallback
  return 'http://localhost:8001'
}

/**
 * Check if fallback data is allowed.
 * Only allowed in development and preview environments.
 */
export function isFallbackAllowed(): boolean {
  return !ENV.isProduction
}
