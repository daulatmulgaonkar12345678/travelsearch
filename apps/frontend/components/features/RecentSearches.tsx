/**
 * Recent Searches Component
 * 
 * Displays the last 3 saved flight searches on the homepage.
 * Data persisted in localStorage - no backend required.
 * Clicking a search re-runs it with the same parameters.
 */

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface SavedSearch {
  origin: string
  destination: string
  departureDate: string
  returnDate?: string
  tripType?: string
  savedAt: string
}

/**
 * Format date for display (YYYY-MM-DD → "Jan 15")
 */
function formatDisplayDate(dateStr: string): string {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr + 'T00:00:00')
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch {
    return dateStr
  }
}

export default function RecentSearches() {
  const router = useRouter()
  const [searches, setSearches] = useState<SavedSearch[]>([])
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // Load saved searches from localStorage
    try {
      const saved = localStorage.getItem('saved_searches')
      if (saved) {
        const parsed = JSON.parse(saved)
        // Only show last 3
        setSearches(parsed.slice(0, 3))
      }
    } catch (e) {
      console.warn('Failed to load saved searches:', e)
    }
  }, [])

  const handleSearchClick = (search: SavedSearch) => {
    // Build search URL and navigate
    const params = new URLSearchParams({
      origin: search.origin,
      destination: search.destination,
      departure_date: search.departureDate,
      trip_type: search.tripType || 'oneway',
      adults: '1',
      cabin_class: 'economy',
    })
    
    if (search.returnDate && search.tripType === 'roundtrip') {
      params.set('return_date', search.returnDate)
    }
    
    router.push(`/flights/results?${params.toString()}`)
  }

  const handleClearAll = () => {
    localStorage.removeItem('saved_searches')
    setSearches([])
  }

  // Don't render if no searches or not mounted (avoid hydration mismatch)
  if (!mounted || searches.length === 0) {
    return null
  }

  return (
    <div 
      className="animate-[fadeIn_0.25s_ease-out]"
      style={{ animationFillMode: 'both' }}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-700">Recent searches</h3>
        <button
          onClick={handleClearAll}
          className="text-xs text-gray-500 hover:text-gray-700 transition-colors"
        >
          Clear all
        </button>
      </div>
      
      <div className="flex flex-wrap gap-2">
        {searches.map((search, index) => (
          <button
            key={`${search.origin}-${search.destination}-${search.departureDate}-${index}`}
            onClick={() => handleSearchClick(search)}
            className="
              group flex items-center gap-2 px-3 py-2 
              bg-white border border-gray-200 rounded-lg
              hover:border-blue-300 hover:bg-blue-50
              transition-all duration-200
              active:scale-[0.98]
            "
            style={{
              animationDelay: `${index * 50}ms`,
              animationFillMode: 'both',
            }}
          >
            {/* Route */}
            <span className="text-sm font-medium text-gray-900">
              {search.origin}
              <span className="text-gray-400 mx-1">→</span>
              {search.destination}
            </span>
            
            {/* Date */}
            <span className="text-xs text-gray-500 border-l border-gray-200 pl-2">
              {formatDisplayDate(search.departureDate)}
              {search.returnDate && search.tripType === 'roundtrip' && (
                <> - {formatDisplayDate(search.returnDate)}</>
              )}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
