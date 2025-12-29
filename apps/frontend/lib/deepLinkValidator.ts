/**
 * Deep Link Validator
 * 
 * MANDATORY: All partner redirects must be validated before opening.
 * This prevents broken affiliate links, user confusion, and trust loss.
 * 
 * Universal Redirect Guard:
 * if (!partnerUrl || partnerUrl.includes("undefined")) {
 *   showFallbackUI();
 *   logError("Invalid vendor redirect blocked");
 *   return;
 * }
 */

export interface ValidationResult {
  isValid: boolean
  error?: string
}

/**
 * Validate a partner URL before redirecting
 * 
 * CHECKS:
 * - URL is not empty
 * - URL does not contain 'undefined'
 * - URL does not contain 'null'
 * - URL starts with http:// or https://
 * - URL does not have broken patterns
 */
export function validatePartnerUrl(url: string | null | undefined): ValidationResult {
  // Check for empty/null URL
  if (!url) {
    return { isValid: false, error: 'URL is empty' }
  }

  // Check for common invalid patterns
  const invalidPatterns = [
    'undefined',
    'null',
    'NaN',
    '-to-undefined',
    'undefined-to-',
    '/undefined/',
    '=undefined',
  ]

  const urlLower = url.toLowerCase()
  
  for (const pattern of invalidPatterns) {
    if (urlLower.includes(pattern)) {
      return { isValid: false, error: `URL contains invalid pattern: ${pattern}` }
    }
  }

  // Check URL starts with valid protocol
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    return { isValid: false, error: 'URL must start with http:// or https://' }
  }

  // Check for double slashes in path (excluding protocol)
  const pathPart = url.replace(/^https?:\/\//, '')
  if (pathPart.includes('//')) {
    return { isValid: false, error: 'URL has malformed path' }
  }

  return { isValid: true }
}

/**
 * Validate hotel deep link params
 * 
 * REQUIRED: city, check_in, check_out
 */
export function validateHotelParams(params: {
  city?: string
  checkIn?: string
  checkOut?: string
}): ValidationResult {
  if (!params.city) {
    return { isValid: false, error: 'City is required' }
  }

  if (!params.checkIn) {
    return { isValid: false, error: 'Check-in date is required' }
  }

  if (!params.checkOut) {
    return { isValid: false, error: 'Check-out date is required' }
  }

  // Validate date format (YYYY-MM-DD)
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/
  
  if (!dateRegex.test(params.checkIn)) {
    return { isValid: false, error: 'Invalid check-in date format' }
  }

  if (!dateRegex.test(params.checkOut)) {
    return { isValid: false, error: 'Invalid check-out date format' }
  }

  // Validate check-out is after check-in
  if (new Date(params.checkOut) <= new Date(params.checkIn)) {
    return { isValid: false, error: 'Check-out must be after check-in' }
  }

  return { isValid: true }
}

/**
 * Log invalid redirect attempt for monitoring
 */
export function logInvalidRedirect(partnerName: string, url: string, error: string): void {
  console.error(`[DeepLink] Invalid redirect blocked: ${partnerName}`, {
    url,
    error,
    timestamp: new Date().toISOString(),
  })
  
  // In production, this would send to error monitoring service
  // e.g., Sentry, LogRocket, etc.
}
