'use client'

/**
 * Refresh Live Price Component
 * 
 * Provides a controlled way for users to refresh flight prices.
 * Integrates with cost-control system:
 * - Sends x-search-intent: "real" header
 * - Checks daily quota and per-IP rate limits
 * - Shows appropriate fallback messages when quota exceeded
 * 
 * CRITICAL RULES:
 * - NEVER auto-refresh prices
 * - ONLY refresh when user explicitly clicks the button
 * - NEVER trigger refresh from filters or UI changes
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { RefreshCw, Clock, Zap, AlertCircle } from 'lucide-react'
import { apiFetch } from '@/lib/api'

interface RefreshLivePriceProps {
  /** Current search parameters */
  searchParams: {
    origin: string
    destination: string
    departureDate: string
    returnDate?: string
    adults: number
    cabinClass: string
    tripType: string
  }
  /** Callback when prices are successfully refreshed */
  onPriceRefresh: (data: RefreshResult) => void
  /** Last updated timestamp (ISO string) */
  lastUpdatedAt?: string
  /** Whether current data is from live API */
  isLive?: boolean
  /** Compact mode for inline display */
  compact?: boolean
}

export interface RefreshResult {
  offers: any[]
  source: 'AMADEUS' | 'CACHE' | 'aviasales'
  isLive: boolean
  lastUpdatedAt: string
  timestampDisplay: string
  quotaExceeded?: boolean
}

type RefreshState = 'idle' | 'loading' | 'success' | 'fallback'

export default function RefreshLivePrice({
  searchParams,
  onPriceRefresh,
  lastUpdatedAt,
  isLive = false,
  compact = false
}: RefreshLivePriceProps) {
  const [state, setState] = useState<RefreshState>('idle')
  const [message, setMessage] = useState<string | null>(null)

  const formatTimestamp = (isoString?: string): string => {
    if (!isoString) return 'just now'
    try {
      // Handle "Updated just now" string
      if (isoString.toLowerCase().includes('just now')) {
        return 'just now'
      }
      const date = new Date(isoString)
      // Check if valid date
      if (isNaN(date.getTime())) {
        return 'recently'
      }
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      })
    } catch {
      return 'recently'
    }
  }

  const handleRefresh = async () => {
    setState('loading')
    setMessage(null)

    try {
      // Build search URL with parameters
      const params = new URLSearchParams({
        origin: searchParams.origin,
        destination: searchParams.destination,
        departure_date: searchParams.departureDate,
        adults: String(searchParams.adults || 1),
        cabin_class: searchParams.cabinClass || 'economy',
        trip_type: searchParams.tripType || 'oneway',
        // Add cache-busting
        request_id: crypto.randomUUID(),
        ts: Date.now().toString()
      })

      if (searchParams.returnDate && searchParams.tripType === 'roundtrip') {
        params.set('return_date', searchParams.returnDate)
      }

      // CRITICAL: Send x-search-intent: "real" to trigger actual API call
      const response = await apiFetch(`/api/search/flights?${params}`, {
        cache: 'no-store',
        headers: {
          'x-search-intent': 'real'  // Triggers real API call with quota check
        }
      })

      if (!response.ok) {
        throw new Error('Failed to refresh prices')
      }

      const data = await response.json()

      // Check if we got live data or fallback
      if (data.source === 'CACHE' || data.is_live === false) {
        setState('fallback')
        setMessage('Live price temporarily unavailable. Showing the most recent available price.')
      } else {
        setState('success')
        setMessage('Live price updated just now')
      }

      // Notify parent with refreshed data
      onPriceRefresh({
        offers: data.offers || data.flights || [],
        source: data.source || 'aviasales',
        isLive: data.is_live ?? true,
        lastUpdatedAt: data.last_live_updated_at || new Date().toISOString(),
        timestampDisplay: data.timestamp_display || 'Updated just now',
        quotaExceeded: data.source === 'CACHE'
      })

      // Clear success message after 3 seconds
      setTimeout(() => {
        if (state === 'success') {
          setState('idle')
          setMessage(null)
        }
      }, 3000)

    } catch (error) {
      console.error('[RefreshLivePrice] Error:', error)
      setState('fallback')
      setMessage('Unable to refresh prices. Please try again.')
    }
  }

  // Compact inline version
  if (compact) {
    return (
      <div className="flex items-center gap-2">
        {/* Timestamp */}
        <span className="text-xs text-gray-500">
          {formatTimestamp(lastUpdatedAt)}
        </span>

        {/* Refresh button */}
        <button
          onClick={handleRefresh}
          disabled={state === 'loading'}
          className="
            inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700
            disabled:text-gray-400 disabled:cursor-not-allowed
            transition-colors
          "
          title="Refresh live price - Prices may change on the booking site"
        >
          <RefreshCw className={`w-3 h-3 ${state === 'loading' ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>
    )
  }

  // Full version with status display
  return (
    <div className="flex flex-col gap-2">
      {/* Timestamp row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isLive ? (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-green-50 text-green-700 border border-green-200 rounded-full font-medium">
              <Zap className="w-3 h-3" />
              Live price
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-amber-50 text-amber-700 border border-amber-200 rounded-full font-medium">
              <Clock className="w-3 h-3" />
              Last known price
            </span>
          )}
          <span className="text-xs text-gray-500">
            {formatTimestamp(lastUpdatedAt)}
          </span>
        </div>

        {/* Refresh button */}
        <motion.button
          onClick={handleRefresh}
          disabled={state === 'loading'}
          whileTap={{ scale: 0.98 }}
          className="
            inline-flex items-center gap-1.5 px-3 py-1.5 text-sm
            text-blue-600 hover:text-blue-700 hover:bg-blue-50
            border border-blue-200 rounded-lg
            disabled:text-gray-400 disabled:border-gray-200 disabled:bg-gray-50 disabled:cursor-not-allowed
            transition-all duration-200
          "
          title="Prices may change on the booking site"
        >
          <RefreshCw className={`w-4 h-4 ${state === 'loading' ? 'animate-spin' : ''}`} />
          {state === 'loading' ? 'Refreshing...' : 'Refresh live price'}
        </motion.button>
      </div>

      {/* Tooltip / Helper text */}
      <p className="text-xs text-gray-500">
        Prices may change on the booking site
      </p>

      {/* Status messages */}
      <AnimatePresence mode="wait">
        {message && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.2 }}
            className={`
              flex items-center gap-2 px-3 py-2 rounded-lg text-sm
              ${state === 'success' 
                ? 'bg-green-50 text-green-700 border border-green-200' 
                : 'bg-amber-50 text-amber-700 border border-amber-200'
              }
            `}
          >
            {state === 'success' ? (
              <Zap className="w-4 h-4" />
            ) : (
              <AlertCircle className="w-4 h-4" />
            )}
            {message}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/**
 * Simple timestamp display with refresh link
 */
export function PriceTimestamp({
  lastUpdatedAt,
  isLive,
  onRefreshClick
}: {
  lastUpdatedAt?: string
  isLive: boolean
  onRefreshClick?: () => void
}) {
  const formatTimestamp = (isoString?: string): string => {
    if (!isoString) return ''
    try {
      const date = new Date(isoString)
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      })
    } catch {
      return ''
    }
  }

  return (
    <div className="flex items-center gap-2 text-xs text-gray-500">
      <span>
        {isLive ? 'Updated just now' : `Last updated at ${formatTimestamp(lastUpdatedAt)}`}
      </span>
      {onRefreshClick && (
        <button
          onClick={onRefreshClick}
          className="text-blue-600 hover:text-blue-700 hover:underline"
        >
          Refresh
        </button>
      )}
    </div>
  )
}
