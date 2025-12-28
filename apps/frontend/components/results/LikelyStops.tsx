'use client'

import { useState, useEffect } from 'react'
import { ChevronDown, ChevronUp, MapPin, Loader2, Route } from 'lucide-react'
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
  const hasCorridorData = data && data.source === 'corridor'

  return (
    <div className="border-t border-gray-100 pt-3 mt-3">
      {/* Toggle Button - 2️⃣ Improved label */}
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
        {expanded && hasAnyStops && (
          <span className="text-xs text-gray-500 font-normal">(Indicative)</span>
        )}
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

          {/* Error State - 2️⃣ Friendly messaging */}
          {error && !loading && (
            <div className="text-sm text-gray-500 py-2">
              <p>This route may follow multiple internal roads.</p>
              <p className="text-xs mt-1">Stops vary by operator and service.</p>
            </div>
          )}

          {/* Data Loaded */}
          {data && !loading && (
            <>
              {/* 2️⃣ No corridor found - Friendly + Trust-Building */}
              {data.source === 'no_corridor' && !hasAnyStops && (
                <div className="text-sm text-gray-600 py-1">
                  <p>This route may follow multiple internal roads.</p>
                  <p className="text-xs text-gray-500 mt-1">Stops vary by operator and service.</p>
                </div>
              )}

              {/* Has stops */}
              {hasAnyStops && (
                <>
                  {/* 2️⃣ Indicative messaging - Subject line */}
                  <p className="text-xs text-gray-500 mb-2">Subject to operator route & service type</p>
                  
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

              {/* No stops found but corridor exists - 2️⃣ Friendly messaging */}
              {!hasAnyStops && hasCorridorData && (
                <div className="text-sm text-gray-600 py-1">
                  <p>Direct route via highway</p>
                  <p className="text-xs text-gray-500 mt-1">Stops vary by operator and service.</p>
                </div>
              )}

              {/* 2️⃣ Disclaimer - Neutral informational tone (NO yellow warning box) */}
              <p className="text-xs text-gray-400 mt-3 leading-relaxed">
                Stops are indicative and may vary by service type and operator.
              </p>
            </>
          )}

          {/* No data loaded yet - 2️⃣ Friendly fallback */}
          {!data && !loading && !error && (
            <div className="text-sm text-gray-500 py-2">
              <p>This route may follow multiple internal roads.</p>
              <p className="text-xs mt-1">Stops vary by operator and service.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
