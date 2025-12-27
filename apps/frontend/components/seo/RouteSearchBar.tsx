'use client'

/**
 * RouteSearchBar - Client-side search bar for route pages
 * 
 * Pre-filled with origin/destination, allows user to:
 * - See the route clearly
 * - Change departure date (defaults to tomorrow)
 * - Adjust passenger count
 * - Click search to go to results
 * 
 * UX PRINCIPLE: Everything auto-filled → user adjusts date → searches
 */

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Calendar, Users, Search, ArrowRight } from 'lucide-react'

interface RouteSearchBarProps {
  originCode: string
  originCity: string
  destinationCode: string
  destinationCity: string
}

/**
 * Get tomorrow's date in YYYY-MM-DD format (default search date)
 */
function getTomorrowDate(): string {
  const date = new Date()
  date.setDate(date.getDate() + 1)
  return date.toISOString().split('T')[0]
}

export default function RouteSearchBar({
  originCode,
  originCity,
  destinationCode,
  destinationCity,
}: RouteSearchBarProps) {
  const router = useRouter()
  const [departureDate, setDepartureDate] = useState(getTomorrowDate())
  const [adults, setAdults] = useState(1)
  const [isSearching, setIsSearching] = useState(false)

  // Get minimum date (today)
  const minDate = new Date().toISOString().split('T')[0]

  const handleSearch = () => {
    setIsSearching(true)
    
    const searchParams = new URLSearchParams({
      origin: originCode,
      destination: destinationCode,
      departure_date: departureDate,
      trip_type: 'oneway',
      adults: String(adults),
      cabin_class: 'economy',
    })
    
    router.push(`/flights/results?${searchParams.toString()}`)
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
      {/* Route display (read-only) */}
      <div className="flex items-center gap-3 mb-6">
        <div className="flex-1 bg-gray-50 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-1">From</p>
          <p className="font-semibold text-gray-900">{originCity}</p>
          <p className="text-sm text-gray-500">{originCode}</p>
        </div>
        
        <div className="flex-shrink-0">
          <ArrowRight className="w-5 h-5 text-gray-400" />
        </div>
        
        <div className="flex-1 bg-gray-50 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-1">To</p>
          <p className="font-semibold text-gray-900">{destinationCity}</p>
          <p className="text-sm text-gray-500">{destinationCode}</p>
        </div>
      </div>

      {/* Editable fields */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        {/* Date picker */}
        <div className="relative">
          <label className="block text-xs text-gray-500 mb-1">Departure Date</label>
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            <input
              type="date"
              value={departureDate}
              min={minDate}
              onChange={(e) => setDepartureDate(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Passengers */}
        <div className="relative">
          <label className="block text-xs text-gray-500 mb-1">Passengers</label>
          <div className="relative">
            <Users className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            <select
              value={adults}
              onChange={(e) => setAdults(Number(e.target.value))}
              className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white cursor-pointer"
            >
              {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(n => (
                <option key={n} value={n}>{n} {n === 1 ? 'Adult' : 'Adults'}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Search button */}
      <button
        onClick={handleSearch}
        disabled={isSearching}
        className="w-full py-4 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 disabled:bg-blue-400"
      >
        {isSearching ? (
          <>
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Searching...
          </>
        ) : (
          <>
            <Search className="w-5 h-5" />
            Search Flights
          </>
        )}
      </button>
      
      <p className="text-xs text-gray-500 text-center mt-3">
        Prices shown are sourced from our travel partners
      </p>
    </div>
  )
}
