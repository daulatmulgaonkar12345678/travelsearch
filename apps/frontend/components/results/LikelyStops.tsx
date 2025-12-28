'use client'

import { useState, useEffect } from 'react'
import { ChevronDown, ChevronUp, MapPin, Info, Loader2, Route } from 'lucide-react'
import { apiFetch } from '@/lib/api'

interface LikelyStopsProps {
  fromCity: string
  toCity: string
}

interface LikelyStopsResponse {
  from_city: string
  to_city: string
  major_stops: string[]  // Always shown - main ST stands
  minor_stops: string[]  // Shown on expand - smaller stops
  corridor_name: string | null
  highway: string | null
  source: string
  note: string
}

export default function LikelyStops({ fromCity, toCity }: LikelyStopsProps) {
  const [expanded, setExpanded] = useState(false)
  const [showMinor, setShowMinor] = useState(false)
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<LikelyStopsResponse | null>(null)
  const [error, setError] = useState(false)

  // Fetch likely stops when expanded
  useEffect(() => {
    if (!expanded || data || loading) return

    const fetchStops = async () => {
      setLoading(true)
      setError(false)
      
      try {
        const params = new URLSearchParams({
          from_city: fromCity,
          to_city: toCity,
        })
        
        const response = await apiFetch(`/api/routes/stops?${params}`)
        
        if (response.ok) {
          const result: LikelyStopsResponse = await response.json()
          setData(result)
        } else {
          setError(true)
        }
      } catch (err) {
        console.error('Failed to fetch likely stops:', err)
        setError(true)
      } finally {
        setLoading(false)
      }
    }

    fetchStops()
  }, [expanded, fromCity, toCity, data, loading])

  const hasMajorStops = data && data.major_stops.length > 0
  const hasMinorStops = data && data.minor_stops.length > 0
  const hasAnyStops = hasMajorStops || hasMinorStops

  return (
    <div className="border-t border-gray-100 pt-3 mt-3">
      {/* Toggle Button */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm text-orange-600 hover:text-orange-800 transition w-full"
        aria-expanded={expanded}
      >
        {expanded ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
        <span className="font-medium">Likely Stops</span>
      </button>

      {/* Expanded Content */}
      {expanded && (
        <div className="mt-3 pl-6">
          {/* Loading State */}
          {loading && (
            <div className="flex items-center gap-2 text-gray-500 text-sm py-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Loading stops...</span>
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <div className="text-sm text-gray-500 py-2">
              <span>Could not load stops for this route.</span>
            </div>
          )}

          {/* Data Loaded */}
          {data && !loading && (
            <>
              {/* No corridor found */}
              {data.source === 'no_corridor' && (
                <p className="text-sm text-gray-500">Direct route - no corridor data available</p>
              )}

              {/* Has stops */}
              {hasAnyStops && (
                <>
                  {/* Header */}
                  <p className="text-xs text-gray-500 mb-2">Likely stops (indicative):</p>
                  
                  {/* MAJOR Stops - Always shown */}
                  {hasMajorStops && (
                    <div className="space-y-1.5 mb-3">
                      {data.major_stops.map((stop, index) => (
                        <div key={`major-${index}`} className="flex items-center gap-2 text-sm text-gray-700">
                          <MapPin className="h-3.5 w-3.5 text-orange-500 flex-shrink-0" />
                          <span className="font-medium">{stop}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* MINOR Stops - Expandable */}
                  {hasMinorStops && (
                    <div className="mt-2">
                      <button
                        onClick={() => setShowMinor(!showMinor)}
                        className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 transition mb-2"
                      >
                        <Route className="h-3 w-3" />
                        {showMinor ? 'Hide' : 'Show'} {data.minor_stops.length} more stop{data.minor_stops.length !== 1 ? 's' : ''}
                        {showMinor ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                      </button>
                      
                      {showMinor && (
                        <div className="space-y-1 pl-2 border-l-2 border-gray-200">
                          {data.minor_stops.map((stop, index) => (
                            <div key={`minor-${index}`} className="flex items-center gap-2 text-sm text-gray-500">
                              <div className="w-1.5 h-1.5 bg-gray-400 rounded-full flex-shrink-0" />
                              <span>{stop}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Corridor/Highway Info */}
                  {data.highway && (
                    <p className="text-xs text-gray-400 mt-3">
                      Via {data.highway}
                      {data.corridor_name && ` (${data.corridor_name})`}
                    </p>
                  )}
                </>
              )}

              {/* No stops found but corridor exists */}
              {!hasAnyStops && data.source === 'corridor' && (
                <p className="text-sm text-gray-500">Direct route - no intermediate stops</p>
              )}

              {/* Disclaimer */}
              <div className="flex items-start gap-1.5 mt-3 p-2 bg-amber-50 rounded text-xs text-amber-700">
                <Info className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" />
                <span>{data.note}</span>
              </div>
            </>
          )}

          {/* No data loaded yet */}
          {!data && !loading && !error && (
            <div className="text-sm text-gray-500 py-2">
              <span>Route information not available.</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
