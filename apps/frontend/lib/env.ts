/**
 * Environment Configuration
 * =========================
 * 
 * SERVER-SIDE ONLY - Used by Next.js API routes
 * 
 * This file is NEVER imported in browser code.
 * BACKEND_URL is only used in API route handlers.
 */

/**
 * Get backend URL for server-side API proxying.
 * Falls back to localhost for local development.
 */
export function getBackendUrl(): string {
  return process.env.BACKEND_URL || 'http://localhost:8001'
}
