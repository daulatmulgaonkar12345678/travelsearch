'use client'

/**
 * PriceSourceBadge Component
 * 
 * Displays trust-building badges for flight search results:
 * - "Live price" (green) - When showing live Amadeus data
 * - "Showing recent prices" (yellow/neutral) - When showing cached data
 * 
 * COMPLIANCE NOTES:
 * - Never shows "Best price today", "Guaranteed price", "Locked price", "Lowest fare"
 * - Never shows alarming language like "Unavailable", "Quota exceeded", "Live search failed"
 * - Always shows honest, trust-building messaging
 */

import { Clock, Zap } from 'lucide-react'

interface PriceSourceBadgeProps {
  /** Whether the results are from live API call */
  isLive: boolean
  /** User-friendly timestamp display (e.g., "Last updated at 08:02 AM") */
  timestampDisplay?: string | null
  /** Additional helper text */
  helperText?: string | null
  /** Size variant */
  size?: 'sm' | 'md'
}

export default function PriceSourceBadge({
  isLive,
  timestampDisplay,
  helperText,
  size = 'sm'
}: PriceSourceBadgeProps) {
  const sizeClasses = size === 'sm' 
    ? 'text-xs px-2 py-1' 
    : 'text-sm px-3 py-1.5'

  if (isLive) {
    // Live price badge - green/positive
    return (
      <div className="flex items-center gap-2">
        <span className={`inline-flex items-center gap-1 ${sizeClasses} bg-green-50 text-green-700 border border-green-200 rounded-full font-medium`}>
          <Zap className="w-3 h-3" />
          Live price
        </span>
        <span className="text-xs text-gray-500">Updated just now</span>
      </div>
    )
  }

  // Cached results badge - yellow/neutral (NEVER red)
  return (
    <div className="flex flex-col gap-0.5">
      <div className="flex items-center gap-2">
        <span className={`inline-flex items-center gap-1 ${sizeClasses} bg-amber-50 text-amber-700 border border-amber-200 rounded-full font-medium`}>
          <Clock className="w-3 h-3" />
          Showing recent prices
        </span>
        {timestampDisplay && (
          <span className="text-xs text-gray-500">{timestampDisplay}</span>
        )}
      </div>
      {helperText && (
        <span className="text-xs text-gray-500">{helperText}</span>
      )}
    </div>
  )
}

/**
 * Compact version for use in flight cards
 */
export function PriceSourceIndicator({ isLive }: { isLive: boolean }) {
  if (isLive) {
    return (
      <span className="inline-flex items-center gap-1 text-xs text-green-600">
        <Zap className="w-3 h-3" />
        Live
      </span>
    )
  }

  return (
    <span className="inline-flex items-center gap-1 text-xs text-amber-600">
      <Clock className="w-3 h-3" />
      Recent
    </span>
  )
}
