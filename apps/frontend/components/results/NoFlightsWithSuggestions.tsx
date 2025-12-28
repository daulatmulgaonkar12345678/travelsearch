'use client'

/**
 * NoFlightsWithSuggestions - Smart "No Results" Page
 * 
 * PRINCIPLES:
 * - A "no results" page must redirect user intent, not block it
 * - Never suggest impossible transport (trains to Texas)
 * - Never burn credits silently (no auto-searches)
 * - Keep users on platform with helpful actions
 * 
 * ROUTE-AWARE BEHAVIOR:
 * - Domestic (PNQ → BOM): Show trains/buses as alternatives
 * - International (PNQ → JFK): Show flight-focused guidance only
 */

import React, { useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { 
  Calendar, 
  MapPin, 
  Info, 
  Plane, 
  Train, 
  Bus, 
  ArrowRight,
  Globe,
  RefreshCw,
  Search
} from 'lucide-react'
import type { FallbackSuggestions } from '@/lib/fallbackSearch'
import { trackFallbackClick } from '@/lib/fallbackSearch'
import { analyzeRouteFeasibility, type RouteFeasibility } from '@/lib/routeFeasibility'

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
  
  // Analyze route feasibility (NO API calls - pure frontend logic)
  const routeInfo = useMemo(() => {
    return analyzeRouteFeasibility(origin, destination)
  }, [origin, destination])
  
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
  
  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleDateString('en-US', { 
      weekday: 'short',
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    })
  }
  
  // Get adjacent dates for suggestions
  const getAdjacentDates = () => {
    const currentDate = new Date(date)
    const prevDate = new Date(currentDate)
    prevDate.setDate(prevDate.getDate() - 1)
    const nextDate = new Date(currentDate)
    nextDate.setDate(nextDate.getDate() + 1)
    
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    
    const dates = []
    if (prevDate >= today) {
      dates.push({
        date: prevDate.toISOString().split('T')[0],
        label: 'Previous day',
        display: formatDate(prevDate.toISOString())
      })
    }
    dates.push({
      date: nextDate.toISOString().split('T')[0],
      label: 'Next day',
      display: formatDate(nextDate.toISOString())
    })
    return dates
  }
  
  const handleDateClick = (newDate: string) => {
    trackFallbackClick('date')
    const params = new URLSearchParams(window.location.search)
    params.set('departure_date', newDate)
    router.push(`/flights/results?${params.toString()}`)
  }
  
  const handleHubClick = (hubCode: string) => {
    trackFallbackClick('hub')
    const params = new URLSearchParams(window.location.search)
    // If origin is Indian, suggest routing via hub
    if (routeInfo.isIndia) {
      params.set('origin', hubCode)
    } else {
      params.set('destination', hubCode)
    }
    router.push(`/flights/results?${params.toString()}`)
  }
  
  const handleAirportClick = (
    newOrigin: string | null, 
    newDestination: string | null
  ) => {
    if (newOrigin) trackFallbackClick('origin')
    if (newDestination) trackFallbackClick('destination')
    
    const params = new URLSearchParams(window.location.search)
    if (newOrigin) params.set('origin', newOrigin)
    if (newDestination) params.set('destination', newDestination)
    
    router.push(`/flights/results?${params.toString()}`)
  }
  
  const handleSurfaceTransport = (mode: 'train' | 'bus') => {
    // Build search URL for trains/buses
    const params = new URLSearchParams({
      origin: origin,
      destination: destination,
      departure_date: date,
      passengers: '1',
    })
    
    if (mode === 'train') {
      // Use station codes or ALL tokens
      router.push(`/trains/results?origin=${origin}_ALL&destination=${destination}_ALL&departure_date=${date}&passengers=1`)
    } else {
      router.push(`/buses/results?${params.toString()}`)
    }
  }
  
  const hasSuggestions = suggestions && (
    suggestions.altDates.length > 0 ||
    suggestions.altOrigins.length > 0 ||
    suggestions.altDestinations.length > 0
  )
  
  const adjacentDates = getAdjacentDates()

  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      {/* Main message - Route-aware */}
      <div className="text-center mb-8">
        <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 ${
          routeInfo.routeType === 'international' ? 'bg-blue-100' : 'bg-amber-100'
        }`}>
          {routeInfo.routeType === 'international' ? (
            <Globe className="w-8 h-8 text-blue-600" />
          ) : (
            <Plane className="w-8 h-8 text-amber-600" />
          )}
        </div>
        
        <h2 className="text-2xl font-bold text-gray-900 mb-3">
          {routeInfo.routeType === 'international' 
            ? 'Flights not available on this route'
            : 'Flights are limited on this route'
          }
        </h2>
        
        <p className="text-gray-600 mb-2">
          <strong>{origin}</strong> → <strong>{destination}</strong> on {formatDate(date)}
        </p>
        
        {/* Route-specific subtext */}
        <p className="text-sm text-gray-500">
          {routeInfo.routeType === 'international' 
            ? 'This route typically requires long-haul or multi-stop international flights.'
            : routeInfo.routeType === 'regional'
            ? 'Direct flights are limited. Consider connecting via major hubs.'
            : 'Surface transport may be more practical for this route.'
          }
        </p>
        
        {isLoadingSuggestions && (
          <p className="text-sm text-blue-600 mt-4 animate-pulse flex items-center justify-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin" />
            Looking for alternative options...
          </p>
        )}
      </div>
      
      {/* ============================================ */}
      {/* DOMESTIC ROUTE: Show Train/Bus Options */}
      {/* ============================================ */}
      {routeInfo.isSurfaceTransportPossible && routeInfo.routeType === 'domestic' && (
        <div className="mb-8 bg-green-50 border border-green-200 rounded-xl p-6">
          <div className="flex items-start gap-3 mb-4">
            <div className="bg-green-100 p-2 rounded-lg">
              <Info className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <h3 className="font-semibold text-green-900">
                Consider surface transport
              </h3>
              <p className="text-sm text-green-700">
                Trains and buses operate frequently on this route and may be more convenient.
              </p>
            </div>
          </div>
          
          <div className="grid sm:grid-cols-2 gap-3">
            <button
              onClick={() => handleSurfaceTransport('train')}
              className="flex items-center gap-3 bg-white border-2 border-green-200 hover:border-green-400 rounded-lg p-4 transition-all hover:shadow-md group"
            >
              <div className="bg-green-100 p-2 rounded-lg group-hover:bg-green-200 transition-colors">
                <Train className="w-5 h-5 text-green-600" />
              </div>
              <div className="text-left flex-1">
                <span className="font-medium text-gray-900 block">Check Trains</span>
                <span className="text-sm text-gray-600">View schedules & book</span>
              </div>
              <ArrowRight className="w-5 h-5 text-green-600 group-hover:translate-x-1 transition-transform" />
            </button>
            
            <button
              onClick={() => handleSurfaceTransport('bus')}
              className="flex items-center gap-3 bg-white border-2 border-green-200 hover:border-green-400 rounded-lg p-4 transition-all hover:shadow-md group"
            >
              <div className="bg-green-100 p-2 rounded-lg group-hover:bg-green-200 transition-colors">
                <Bus className="w-5 h-5 text-green-600" />
              </div>
              <div className="text-left flex-1">
                <span className="font-medium text-gray-900 block">Check Buses</span>
                <span className="text-sm text-gray-600">View options & prices</span>
              </div>
              <ArrowRight className="w-5 h-5 text-green-600 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      )}
      
      {/* ============================================ */}
      {/* INTERNATIONAL ROUTE: Flight-focused guidance */}
      {/* ============================================ */}
      {!routeInfo.isSurfaceTransportPossible && (
        <div className="mb-8 space-y-6">
          
          {/* Try major international hubs */}
          {routeInfo.suggestedHubs.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
              <div className="flex items-start gap-3 mb-4">
                <div className="bg-blue-100 p-2 rounded-lg">
                  <Plane className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-blue-900">
                    Try major international hubs
                  </h3>
                  <p className="text-sm text-blue-700">
                    More flights connect through these airports:
                  </p>
                </div>
              </div>
              
              <div className="grid sm:grid-cols-3 gap-3">
                {routeInfo.suggestedHubs.slice(0, 3).map((hub) => (
                  <button
                    key={hub.code}
                    onClick={() => handleHubClick(hub.code)}
                    className="bg-white border-2 border-blue-200 hover:border-blue-400 rounded-lg p-4 text-left transition-all hover:shadow-md group"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-bold text-blue-600">{hub.code}</span>
                      <span className="text-sm text-gray-600">{hub.name}</span>
                    </div>
                    <p className="text-xs text-gray-500 mb-2">{hub.fullName}</p>
                    <span className="text-sm text-blue-600 group-hover:underline flex items-center gap-1">
                      Search via {hub.code}
                      <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
          
          {/* Try nearby dates */}
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-6">
            <div className="flex items-start gap-3 mb-4">
              <div className="bg-gray-100 p-2 rounded-lg">
                <Calendar className="w-5 h-5 text-gray-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">
                  Try nearby dates
                </h3>
                <p className="text-sm text-gray-600">
                  Some routes have flights only on specific days:
                </p>
              </div>
            </div>
            
            <div className="grid sm:grid-cols-2 gap-3">
              {adjacentDates.map((d) => (
                <button
                  key={d.date}
                  onClick={() => handleDateClick(d.date)}
                  className="bg-white border-2 border-gray-200 hover:border-gray-400 rounded-lg p-4 text-left transition-all hover:shadow-md group"
                >
                  <span className="text-sm text-gray-500 block mb-1">{d.label}</span>
                  <span className="font-medium text-gray-900 block">{d.display}</span>
                  <span className="text-sm text-blue-600 group-hover:underline mt-2 flex items-center gap-1">
                    Search this date
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* ============================================ */}
      {/* API Suggestions (if available) */}
      {/* ============================================ */}
      {!isLoadingSuggestions && hasSuggestions && (
        <div className="mb-8 space-y-6">
          <p className="text-center text-gray-700 font-medium">
            Other options that might work:
          </p>
          
          {/* Alternative Dates from API */}
          {suggestions.altDates.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Calendar className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-gray-900">Flights on other dates</h3>
              </div>
              
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {suggestions.altDates.slice(0, 3).map((alt) => (
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
                {suggestions.altOrigins.slice(0, 2).map((alt) => (
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
                {suggestions.altDestinations.slice(0, 2).map((alt) => (
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
      
      {/* Action buttons */}
      <div className="flex gap-4 justify-center flex-wrap pt-4 border-t border-gray-200">
        <button
          onClick={() => router.push('/')}
          className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white hover:bg-gray-50 text-gray-900 font-medium rounded-lg border-2 border-gray-300 transition-colors"
        >
          <Search className="w-4 h-4" />
          Modify Search
        </button>
        <button
          onClick={onTryAgain}
          className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          New Search
        </button>
      </div>
    </div>
  )
}
