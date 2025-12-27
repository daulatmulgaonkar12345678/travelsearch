'use client'

import { useState, useEffect } from 'react'
import { ChevronDown, ChevronUp, MapPin, Info, Loader2 } from 'lucide-react'
import { apiFetch } from '@/lib/api'

interface LikelyStopsProps {
  fromCity: string
  toCity: string
}

interface LikelyStopsResponse {
  from_city: string
  to_city: string
  likely_stops: string[]
  corridor_name: string | null
  highway: string | null
  stop_count: number
  note: string
  source: string
}

export default function LikelyStops({ fromCity, toCity }: LikelyStopsProps) {
  const [expanded, setExpanded] = useState(false)
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
          max_stops: '5',
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
          {loading && (
            <div className="flex items-center gap-2 text-gray-500 text-sm py-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Loading stops...</span>
            </div>
          )}

          {error && !loading && (
            <div className="text-sm text-gray-500 py-2">
              <span>Could not load stops for this route.</span>
            </div>
          )}

          {data && !loading && (
            <>
              {/* Likely Stops Header */}
              <p className="text-xs text-gray-500 mb-2">Likely stops (indicative):</p>
              
              {/* Stops List */}
              {data.stop_count > 0 ? (
                <div className="space-y-1.5">
                  {data.likely_stops.map((stop, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm text-gray-700">
                      <MapPin className="h-3.5 w-3.5 text-orange-500 flex-shrink-0" />
                      <span>{stop}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">Direct route - no intermediate stops</p>
              )}

              {/* Corridor/Highway Info */}
              {data.highway && (
                <p className="text-xs text-gray-400 mt-2">
                  Via {data.highway}
                  {data.corridor_name && ` (${data.corridor_name})`}
                </p>
              )}

              {/* Disclaimer */}
              <div className="flex items-start gap-1.5 mt-3 p-2 bg-amber-50 rounded text-xs text-amber-700">
                <Info className="h-3.5 w-3.5 flex-shrink-0 mt-0.5" />
                <span>{data.note}</span>
              </div>
            </>
          )}

          {/* Direct route fallback when no data */}
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
