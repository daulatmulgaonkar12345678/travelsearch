'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import BusCard from '@/components/results/BusCard'
import TransportLoadingState from '@/components/loading/TransportLoadingState'
import { Loader2, Bus, ArrowLeft, AlertCircle, Filter, SlidersHorizontal, Clock, MapPin } from 'lucide-react'
import { apiFetch } from '@/lib/api'
import { addRecentSearch, updateRecentSearchPrice } from '@/lib/unifiedRecentSearchStore'
import NoResultsState from '@/components/common/NoResultsState'
import ServiceError, { getErrorType, ErrorType } from '@/components/common/ServiceError'

interface BusOffer {
  offer_id: string
  mode: string
  provider: string
  from_station: string
  from_city: string
  from_station_name: string
  to_station: string
  to_city: string
  to_station_name: string
  departure_time: string
  arrival_time: string
  duration_minutes: number
  avg_price: number
  currency: string
  price_label: string
  price_disclaimer: string
  distance_km: number | null
  booking_partners: Array<{
    name: string
    url: string
    priority: number
    is_official?: boolean
  }>
  is_fallback: boolean
  operator_name: string
  operator_type: string
  bus_type: string
  bus_type_label: string
  is_ac: boolean
  is_sleeper: boolean
  has_charging_point: boolean
  has_wifi: boolean
  frequency: string | null
  departure_window: string | null
  stops_count: number
  intermediate_stops: string[]
}

interface BusSearchResponse {
  offers: BusOffer[]
  search_id: string
  cached: boolean
  timestamp: string
  origin_city: string
  destination_city: string
  distance_km: number | null
  is_fallback: boolean
  fallback_message: string | null
}

// Bus type options (matching Flight filter experience)
const BUS_TYPES = [
  { value: 'non_ac', label: 'Non-AC Seater', filter: (o: BusOffer) => !o.is_ac && !o.is_sleeper },
  { value: 'ac_seater', label: 'AC Seater', filter: (o: BusOffer) => o.is_ac && !o.is_sleeper },
  { value: 'ac_sleeper', label: 'AC Sleeper', filter: (o: BusOffer) => o.is_ac && o.is_sleeper },
  { value: 'non_ac_sleeper', label: 'Non-AC Sleeper', filter: (o: BusOffer) => !o.is_ac && o.is_sleeper },
]

// Operator types
const OPERATOR_TYPES = [
  { value: 'government', label: 'Government (RTC)' },
  { value: 'private', label: 'Private' },
]

// Departure time slots (same as trains/flights)
const TIME_SLOTS = [
  { value: 'early_morning', label: 'Early Morning (00:00-06:00)', min: 0, max: 6 },
  { value: 'morning', label: 'Morning (06:00-12:00)', min: 6, max: 12 },
  { value: 'afternoon', label: 'Afternoon (12:00-18:00)', min: 12, max: 18 },
  { value: 'evening', label: 'Evening (18:00-24:00)', min: 18, max: 24 },
]

// 5️⃣ Helper to format city name - extracts main city and station separately
const formatRouteCity = (cityName: string, stationName?: string): { main: string; station: string | null } => {
  // Common station suffixes to extract
  const suffixes = ['Swargate', 'CBS', 'Central', 'Junction', 'Bus Stand', 'Bus Station', 'Depot', 'Terminal']
  
  let main = cityName
  let station: string | null = null
  
  // Check if city name contains a station suffix
  for (const suffix of suffixes) {
    if (cityName.toLowerCase().includes(suffix.toLowerCase())) {
      // Extract just the city name
      const parts = cityName.split(/\s+/)
      const suffixIndex = parts.findIndex(p => p.toLowerCase().includes(suffix.toLowerCase().split(' ')[0]))
      if (suffixIndex > 0) {
        main = parts.slice(0, suffixIndex).join(' ')
        station = parts.slice(suffixIndex).join(' ')
      }
      break
    }
  }
  
  // If station name provided separately and different from city
  if (stationName && stationName !== cityName && !station) {
    // Extract station identifier from station name
    const stationParts = stationName.split(/[()]/)[1] || stationName.split(' ').pop()
    if (stationParts && stationParts !== main) {
      station = stationParts
    }
  }
  
  return { main, station }
}

function BusResultsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  
  const origin = searchParams.get('origin') || ''
  const destination = searchParams.get('destination') || ''
  const departureDate = searchParams.get('departure_date') || ''
  const initialBusType = searchParams.get('bus_type') || ''
  const passengers = searchParams.get('passengers') || '1'
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<ErrorType | null>(null)
  const [results, setResults] = useState<BusSearchResponse | null>(null)
  
  // Sorting (same options as flights)
  const [sortBy, setSortBy] = useState<'price' | 'departure' | 'duration'>('price')
  
  // Filters (matching flight filter experience)
  const [showFilters, setShowFilters] = useState(false)
  const [selectedBusTypes, setSelectedBusTypes] = useState<string[]>(initialBusType ? [initialBusType] : [])
  const [selectedOperatorTypes, setSelectedOperatorTypes] = useState<string[]>([])
  const [selectedTimeSlots, setSelectedTimeSlots] = useState<string[]>([])
  const [maxPrice, setMaxPrice] = useState<number | null>(null)
  const [acOnly, setAcOnly] = useState(false)
  const [sleeperOnly, setSleeperOnly] = useState(false)
  
  useEffect(() => {
    const fetchBuses = async () => {
      if (!origin || !destination || !departureDate) {
        setError('Missing search parameters')
        setLoading(false)
        return
      }
      
      try {
        setLoading(true)
        setError(null)
        
        const params = new URLSearchParams({
          origin,
          destination,
          departure_date: departureDate,
          passengers,
        })
        
        const response = await apiFetch(`/api/search/buses?${params}`)
        
        if (!response.ok) {
          // Log for developers, show friendly error to users
          const errorData = await response.json().catch(() => ({}))
          console.error('[BusSearch] API Error:', response.status, errorData)
          setError(getErrorType(response.status))
          return
        }
        
        const data: BusSearchResponse = await response.json()
        setResults(data)
        
        // Save to recent searches
        addRecentSearch({
          mode: 'bus',
          origin: data.origin_city || origin,
          destination: data.destination_city || destination,
          departureDate,
          passengers: parseInt(passengers),
          busType: initialBusType || undefined,
        })
        
        // Update price if we have results
        if (data.offers.length > 0 && !data.is_fallback) {
          const lowestPrice = Math.min(...data.offers.map(o => o.avg_price))
          updateRecentSearchPrice('bus', origin, destination, departureDate, lowestPrice, 'INR')
        }
        
      } catch (err) {
        console.error('[BusSearch] Fetch error:', err)
        setError(getErrorType(undefined, err instanceof Error ? err : undefined))
      } finally {
        setLoading(false)
      }
    }
    
    fetchBuses()
  }, [origin, destination, departureDate, passengers, initialBusType])
  
  // Filter and sort offers
  const getFilteredAndSortedOffers = () => {
    if (!results?.offers) return []
    
    let filtered = results.offers.filter(offer => {
      // Skip fallback in filtering
      if (offer.is_fallback) return true
      
      // Filter by bus type
      if (selectedBusTypes.length > 0) {
        const matchesType = selectedBusTypes.some(typeValue => {
          const typeConfig = BUS_TYPES.find(t => t.value === typeValue)
          return typeConfig?.filter(offer)
        })
        if (!matchesType) return false
      }
      
      // Filter by operator type
      if (selectedOperatorTypes.length > 0) {
        if (!selectedOperatorTypes.includes(offer.operator_type)) return false
      }
      
      // Filter by time slot
      if (selectedTimeSlots.length > 0) {
        const depHour = new Date(offer.departure_time).getHours()
        const matchesSlot = selectedTimeSlots.some(slot => {
          const timeSlot = TIME_SLOTS.find(t => t.value === slot)
          if (!timeSlot) return false
          return depHour >= timeSlot.min && depHour < timeSlot.max
        })
        if (!matchesSlot) return false
      }
      
      // Filter by price
      if (maxPrice !== null && offer.avg_price > maxPrice) return false
      
      // Filter AC only
      if (acOnly && !offer.is_ac) return false
      
      // Filter sleeper only
      if (sleeperOnly && !offer.is_sleeper) return false
      
      return true
    })
    
    // Sort (fallback always at end)
    filtered.sort((a, b) => {
      if (a.is_fallback) return 1
      if (b.is_fallback) return -1
      
      switch (sortBy) {
        case 'price':
          return a.avg_price - b.avg_price
        case 'departure':
          return new Date(a.departure_time).getTime() - new Date(b.departure_time).getTime()
        case 'duration':
          return a.duration_minutes - b.duration_minutes
        default:
          return 0
      }
    })
    
    return filtered
  }
  
  const filteredOffers = getFilteredAndSortedOffers()
  const hasActiveFilters = selectedBusTypes.length > 0 || selectedOperatorTypes.length > 0 || 
                           selectedTimeSlots.length > 0 || maxPrice !== null || acOnly || sleeperOnly
  
  const clearFilters = () => {
    setSelectedBusTypes([])
    setSelectedOperatorTypes([])
    setSelectedTimeSlots([])
    setMaxPrice(null)
    setAcOnly(false)
    setSleeperOnly(false)
  }
  
  const toggleBusType = (type: string) => {
    setSelectedBusTypes(prev => 
      prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
    )
  }
  
  const toggleOperatorType = (type: string) => {
    setSelectedOperatorTypes(prev => 
      prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
    )
  }
  
  const toggleTimeSlot = (slot: string) => {
    setSelectedTimeSlots(prev => 
      prev.includes(slot) ? prev.filter(s => s !== slot) : [...prev, slot]
    )
  }
  
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    })
  }
  
  // Get price range for filter
  const priceRange = results?.offers
    .filter(o => !o.is_fallback)
    .reduce((acc, o) => ({
      min: Math.min(acc.min, o.avg_price),
      max: Math.max(acc.max, o.avg_price),
    }), { min: Infinity, max: 0 }) || { min: 0, max: 5000 }
  
  // 5️⃣ Format route header with station in parentheses
  const originCity = results?.origin_city || origin
  const destCity = results?.destination_city || destination
  const originFormatted = formatRouteCity(originCity)
  const destFormatted = formatRouteCity(destCity)
  
  // Check if results are estimated (state network or fallback with offers)
  const hasEstimatedResults = results && (
    results.is_fallback || 
    results.offers.some(o => o.provider === 'state_network' || o.operator_name === 'Multiple Operators')
  )
  
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => router.push('/')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to search
          </button>
          
          <div className="flex items-center justify-between">
            <div>
              {/* 5️⃣ Improved Route Header */}
              <div className="flex items-center gap-3 mb-2">
                <Bus className="h-6 w-6 text-orange-600" />
                <h1 className="text-2xl font-bold text-gray-900">
                  Buses from {originFormatted.main} → {destFormatted.main}
                  {(originFormatted.station || destFormatted.station) && (
                    <span className="text-lg font-normal text-gray-500 ml-2">
                      {originFormatted.station && `(${originFormatted.station})`}
                      {originFormatted.station && destFormatted.station && ' to '}
                      {destFormatted.station && `(${destFormatted.station})`}
                    </span>
                  )}
                </h1>
              </div>
              <div className="flex items-center gap-3 text-gray-600">
                <span>{formatDate(departureDate)} • {passengers} passenger{parseInt(passengers) > 1 ? 's' : ''}</span>
                {/* 5️⃣ Subject to availability note */}
                {hasEstimatedResults && (
                  <span className="text-xs text-gray-400">• Subject to service availability</span>
                )}
              </div>
            </div>
            
            {/* Filter toggle button */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition ${
                hasActiveFilters 
                  ? 'border-orange-500 bg-orange-50 text-orange-700' 
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <SlidersHorizontal className="h-4 w-4" />
              Filters
              {hasActiveFilters && (
                <span className="bg-orange-600 text-white text-xs px-1.5 py-0.5 rounded-full">
                  {selectedBusTypes.length + selectedOperatorTypes.length + selectedTimeSlots.length + (maxPrice ? 1 : 0) + (acOnly ? 1 : 0) + (sleeperOnly ? 1 : 0)}
                </span>
              )}
            </button>
          </div>
        </div>
        
        {/* Filters Panel */}
        {showFilters && (
          <div className="bg-white rounded-lg border shadow-sm p-4 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium text-gray-900">Filter Results</h3>
              {hasActiveFilters && (
                <button onClick={clearFilters} className="text-sm text-orange-600 hover:text-orange-800">
                  Clear all
                </button>
              )}
            </div>
            
            <div className="grid md:grid-cols-4 gap-6">
              {/* Bus Type */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Bus Type</h4>
                <div className="space-y-2">
                  {BUS_TYPES.map(type => (
                    <label key={type.value} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedBusTypes.includes(type.value)}
                        onChange={() => toggleBusType(type.value)}
                        className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                      />
                      <span className="text-sm text-gray-600">{type.label}</span>
                    </label>
                  ))}
                </div>
              </div>
              
              {/* Operator Type */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Operator</h4>
                <div className="space-y-2">
                  {OPERATOR_TYPES.map(type => (
                    <label key={type.value} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedOperatorTypes.includes(type.value)}
                        onChange={() => toggleOperatorType(type.value)}
                        className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                      />
                      <span className="text-sm text-gray-600">{type.label}</span>
                    </label>
                  ))}
                </div>
                
                <h4 className="text-sm font-medium text-gray-700 mt-4 mb-2">Amenities</h4>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={acOnly}
                      onChange={(e) => setAcOnly(e.target.checked)}
                      className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                    />
                    <span className="text-sm text-gray-600">AC Only</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={sleeperOnly}
                      onChange={(e) => setSleeperOnly(e.target.checked)}
                      className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                    />
                    <span className="text-sm text-gray-600">Sleeper Only</span>
                  </label>
                </div>
              </div>
              
              {/* Departure Time */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Departure Time</h4>
                <div className="space-y-2">
                  {TIME_SLOTS.map(slot => (
                    <label key={slot.value} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedTimeSlots.includes(slot.value)}
                        onChange={() => toggleTimeSlot(slot.value)}
                        className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
                      />
                      <span className="text-sm text-gray-600">{slot.label}</span>
                    </label>
                  ))}
                </div>
              </div>
              
              {/* Price Range */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  Max Price: {maxPrice ? `₹${maxPrice.toLocaleString()}` : 'Any'}
                </h4>
                <input
                  type="range"
                  min={priceRange.min}
                  max={priceRange.max}
                  value={maxPrice || priceRange.max}
                  onChange={(e) => setMaxPrice(parseInt(e.target.value))}
                  className="w-full accent-orange-600"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>₹{priceRange.min}</span>
                  <span>₹{priceRange.max}</span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Sort Controls (same as flights) */}
        {!loading && !error && results && !results.is_fallback && filteredOffers.length > 1 && (
          <div className="flex items-center gap-4 mb-6">
            <span className="text-sm text-gray-600">Sort by:</span>
            <div className="flex gap-2">
              {(['price', 'departure', 'duration'] as const).map(option => (
                <button
                  key={option}
                  onClick={() => setSortBy(option)}
                  className={`px-3 py-1 text-sm rounded-full transition ${
                    sortBy === option
                      ? 'bg-orange-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {option === 'price' ? 'Cheapest' : option === 'departure' ? 'Earliest' : 'Fastest'}
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* Loading State - Service-specific animation */}
        {loading && (
          <TransportLoadingState 
            mode="bus"
            origin={originFormatted.main}
            destination={destFormatted.main}
          />
        )}
        
        {/* Error State - User-friendly */}
        {error && (
          <ServiceError 
            type={error}
            onRetry={() => window.location.reload()}
            onGoBack={() => router.push('/')}
          />
        )}
        
        {/* No Results State - when search succeeded but empty */}
        {!loading && !error && results && results.offers.length === 0 && (
          <NoResultsState
            service="bus"
            origin={origin}
            destination={destination}
            date={departureDate}
            onChangeDate={() => router.push(`/?tab=buses&origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}`)}
            onModifySearch={() => router.push('/?tab=buses')}
            onGoBack={() => router.push('/')}
          />
        )}
        
        {/* Results */}
        {!loading && !error && results && results.offers.length > 0 && (
          <>
            {/* 4️⃣ Improved Fallback Notice - Confidence-based */}
            {results.is_fallback && results.offers.length > 0 && (
              <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <Bus className="h-5 w-5 text-orange-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900 mb-1">Buses are available on this route</p>
                    <p className="text-sm text-gray-600">
                      Live schedules may vary by operator and date. We've shown typical timings and fares based on common services.
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Summary Stats - Duration-focused, no distance */}
            {filteredOffers.filter(o => !o.is_fallback).length > 0 && (
              <div className="flex flex-wrap items-center gap-4 mb-4 text-sm text-gray-600">
                <span className="flex items-center gap-1.5">
                  🚌 {filteredOffers.filter(o => !o.is_fallback).length} bus{filteredOffers.filter(o => !o.is_fallback).length !== 1 ? 'es' : ''} found
                </span>
                {filteredOffers.filter(o => !o.is_fallback).length > 0 && (
                  <span className="flex items-center gap-1.5">
                    💰 From ₹{Math.min(...filteredOffers.filter(o => !o.is_fallback).map(o => Math.round(o.avg_price))).toLocaleString('en-IN')}
                  </span>
                )}
                {hasActiveFilters && results.offers.length !== filteredOffers.length && (
                  <span className="text-orange-600">(filtered from {results.offers.length})</span>
                )}
              </div>
            )}
            
            {/* No results after filter */}
            {filteredOffers.length === 0 && hasActiveFilters && (
              <div className="text-center py-8 bg-white rounded-lg border">
                <Filter className="h-8 w-8 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600">No buses match your filters</p>
                <button 
                  onClick={clearFilters}
                  className="mt-2 text-orange-600 hover:text-orange-800 text-sm"
                >
                  Clear filters
                </button>
              </div>
            )}
            
            {/* Bus Cards */}
            <div className="space-y-4">
              {filteredOffers.map((offer, idx) => (
                <BusCard key={offer.offer_id} offer={offer} index={idx} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default function BusResultsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-orange-600" />
      </div>
    }>
      <BusResultsContent />
    </Suspense>
  )
}
