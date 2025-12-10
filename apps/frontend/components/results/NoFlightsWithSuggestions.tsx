'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { Calendar, MapPin, Info } from 'lucide-react'
import type { FallbackSuggestions } from '@/lib/fallbackSearch'
import { trackFallbackClick } from '@/lib/fallbackSearch'

interface NoFlightsWithSuggestionsProps {
  origin: string
  destination: string
  date: string
  tripType: string
  suggestions: FallbackSuggestions | null
  isLoadingSuggestions: boolean
  onTryAgain: () => void
}

export default function NoFlightsWithSuggestions({
  origin,
  destination,
  date,
  tripType,
  suggestions,
  isLoadingSuggestions,
  onTryAgain
}: NoFlightsWithSuggestionsProps) {
  const router = useRouter()
  
  const formatDuration = (minutes: number): string => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (hours === 0) return `${mins}m`
    if (mins === 0) return `${hours}h`
    return `${hours}h ${mins}m`
  }
  
  const formatPrice = (price: number): string => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(price)
  }
  
  const handleDateClick = (newDate: string) => {
    trackFallbackClick('date')
    
    // Build new search URL
    const params = new URLSearchParams(window.location.search)
    params.set('departure_date', newDate)
    
    router.push(`/flights/results?${params.toString()}`)
  }
  
  const handleAirportClick = (
    newOrigin: string | null, 
    newDestination: string | null
  ) => {
    if (newOrigin) trackFallbackClick('origin')
    if (newDestination) trackFallbackClick('destination')
    
    // Build new search URL
    const params = new URLSearchParams(window.location.search)
    if (newOrigin) params.set('origin', newOrigin)
    if (newDestination) params.set('destination', newDestination)
    
    router.push(`/flights/results?${params.toString()}`)
  }
  
  const hasSuggestions = suggestions && (
    suggestions.altDates.length > 0 ||
    suggestions.altOrigins.length > 0 ||
    suggestions.altDestinations.length > 0
  )
  
  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      {/* Main message */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
          <svg
            className="w-8 h-8 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          No flights found
        </h2>
        
        <p className="text-gray-600 mb-1">
          We couldn't find any flights from <strong>{origin}</strong> to{' '}
          <strong>{destination}</strong> on{' '}
          <strong>{new Date(date).toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric',
            year: 'numeric'
          })}</strong>.
        </p>
        
        {isLoadingSuggestions && (
          <p className="text-sm text-blue-600 mt-4 animate-pulse">
            Looking for alternative options...
          </p>
        )}
      </div>
      
      {/* Suggestions */}
      {!isLoadingSuggestions && hasSuggestions && (
        <div className="mb-8 space-y-6">
          <p className="text-center text-gray-700 font-medium">
            But here are some options that might work:
          </p>
          
          {/* Alternative Dates */}
          {suggestions.altDates.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Calendar className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-gray-900">Alternative dates</h3>
              </div>
              
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {suggestions.altDates.map((alt) => (
                  <button
                    key={alt.date}
                    onClick={() => handleDateClick(alt.date)}
                    className="bg-white border-2 border-gray-200 hover:border-blue-500 rounded-lg p-4 text-left transition-all hover:shadow-md group"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-sm font-medium text-gray-900">
                        {alt.displayDate}
                      </span>
                      <span className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">
                        {alt.offerCount} flights
                      </span>
                    </div>
                    
                    <div className="text-lg font-bold text-blue-600 mb-1">
                      from {formatPrice(alt.minPrice)}
                    </div>
                    
                    <div className="text-sm text-gray-600">
                      {formatDuration(alt.minDuration)}
                    </div>
                    
                    <div className="mt-2 text-sm text-blue-600 group-hover:underline">
                      View flights →
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {/* Nearby Origin Airports */}
          {suggestions.altOrigins.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <MapPin className="w-5 h-5 text-green-600" />
                <h3 className="font-semibold text-gray-900">Nearby departure airports</h3>
              </div>
              
              <div className="grid gap-3 sm:grid-cols-2">
                {suggestions.altOrigins.map((alt) => (
                  <button
                    key={alt.iata}
                    onClick={() => handleAirportClick(alt.iata, null)}
                    className="bg-white border-2 border-gray-200 hover:border-green-500 rounded-lg p-4 text-left transition-all hover:shadow-md group"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <span className="text-sm font-bold text-gray-900">
                          {alt.iata}
                        </span>
                        <span className="text-sm text-gray-600 ml-2">
                          {alt.city}
                        </span>
                      </div>
                      <span className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded">
                        {alt.distance_km.toFixed(0)} km away
                      </span>
                    </div>
                    
                    <div className="text-sm text-gray-700 mb-1">
                      From <strong>{alt.iata}</strong> to <strong>{destination}</strong>
                    </div>
                    
                    <div className="text-lg font-bold text-green-600 mb-1">
                      from {formatPrice(alt.minPrice)}
                    </div>
                    
                    <div className="text-sm text-gray-600">
                      {formatDuration(alt.minDuration)} • {alt.offerCount} flights
                    </div>
                    
                    <div className="mt-2 text-sm text-green-600 group-hover:underline">
                      View flights →
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {/* Nearby Destination Airports */}
          {suggestions.altDestinations.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <MapPin className="w-5 h-5 text-purple-600" />
                <h3 className="font-semibold text-gray-900">Nearby arrival airports</h3>
              </div>
              
              <div className="grid gap-3 sm:grid-cols-2">
                {suggestions.altDestinations.map((alt) => (
                  <button
                    key={alt.iata}
                    onClick={() => handleAirportClick(null, alt.iata)}
                    className="bg-white border-2 border-gray-200 hover:border-purple-500 rounded-lg p-4 text-left transition-all hover:shadow-md group"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <span className="text-sm font-bold text-gray-900">
                          {alt.iata}
                        </span>
                        <span className="text-sm text-gray-600 ml-2">
                          {alt.city}
                        </span>
                      </div>
                      <span className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded">
                        {alt.distance_km.toFixed(0)} km away
                      </span>
                    </div>
                    
                    <div className="text-sm text-gray-700 mb-1">
                      From <strong>{origin}</strong> to <strong>{alt.iata}</strong>
                    </div>
                    
                    <div className="text-lg font-bold text-purple-600 mb-1">
                      from {formatPrice(alt.minPrice)}
                    </div>
                    
                    <div className="text-sm text-gray-600">
                      {formatDuration(alt.minDuration)} • {alt.offerCount} flights
                    </div>
                    
                    <div className="mt-2 text-sm text-purple-600 group-hover:underline">
                      View flights →
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Tips section (when no suggestions) */}
      {!isLoadingSuggestions && !hasSuggestions && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-gray-700 space-y-2">
              <p className="font-medium text-gray-900">Tips to find flights:</p>
              <ul className="space-y-1 list-disc list-inside">
                <li>Try major hub airports near your destination (e.g., ATH instead of smaller regional airports)</li>
                <li>Try changing your dates or consider a different day of the week</li>
                <li>Some routes are seasonal or not available every day</li>
                <li>Consider connecting flights through major hubs</li>
                {tripType === 'oneway' && (
                  <li>Try searching for a round-trip instead - sometimes it reveals more options</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}
      
      {/* Try another search button */}
      <div className="text-center">
        <button
          onClick={onTryAgain}
          className="inline-flex items-center justify-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
        >
          Try another search
        </button>
      </div>
    </div>
  )
}
