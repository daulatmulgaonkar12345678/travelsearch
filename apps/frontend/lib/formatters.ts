/**
 * Formatting Utilities
 * 
 * Centralized formatting functions for consistent display across the app.
 */

/**
 * Format flight duration in minutes to human-readable string
 * 
 * @param minutes - Total duration in minutes
 * @returns Formatted string like "4h 05m" or "45m"
 * 
 * @example
 * formatDuration(245) // "4h 05m"
 * formatDuration(45)  // "45m"
 * formatDuration(180) // "3h 00m"
 */
export function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${minutes}m`
  }

  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60

  // Always show two-digit minutes when hours are present
  return `${hours}h ${mins.toString().padStart(2, '0')}m`
}

/**
 * Format price with proper locale formatting
 * 
 * @param price - Price amount
 * @param currency - Currency code (default: 'INR')
 * @returns Formatted price string
 */
export function formatPrice(price: number, currency: string = 'INR'): string {
  return `${currency} ${Math.round(price).toLocaleString()}`
}

/**
 * Format time from ISO string to HH:MM
 * 
 * @param isoDate - ISO date string
 * @returns Formatted time string like "14:30"
 */
export function formatTime(isoDate: string): string {
  const date = new Date(isoDate)
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit', 
    hour12: false 
  })
}

/**
 * Format date to readable string
 * 
 * @param dateStr - Date string (YYYY-MM-DD or ISO)
 * @returns Formatted date like "Dec 20, 2025"
 */
export function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}
