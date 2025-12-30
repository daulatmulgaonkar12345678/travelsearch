'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import TrainCard from '@/components/results/TrainCard'
import TrainRedirectCard from '@/components/results/TrainRedirectCard'
import TransportLoadingState from '@/components/loading/TransportLoadingState'
import { Loader2, Train, ArrowLeft, AlertCircle, Filter, SlidersHorizontal } from 'lucide-react'
import { apiFetch } from '@/lib/api'
import { addRecentSearch, updateRecentSearchPrice } from '@/lib/unifiedRecentSearchStore'
import NoResultsState from '@/components/common/NoResultsState'
import ServiceError, { getErrorType, ErrorType } from '@/components/common/ServiceError'
import ModifySearchButton from '@/components/search/ModifySearchButton'

interface TrainOffer {
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
  train_number: string
  train_name: string
  train_type: string | null
  days_of_operation: string[]
  frequency: string | null
  stops_count: number
  intermediate_stops: string[]
  available_classes: Array<{ class: string; avg_fare: number }>
  has_pantry: boolean
}

interface TrainSearchResponse {
  offers: TrainOffer[]
  search_id: string
  cached: boolean
  timestamp: string
  origin_city: string
  destination_city: string
  distance_km: number | null
  is_fallback: boolean
  fallback_message: string | null
}

// Train class options
const TRAIN_CLASSES = [
  { value: 'SL', label: 'Sleeper (SL)' },
  { value: 'CC', label: 'Chair Car (CC)' },
  { value: '3A', label: 'AC 3-Tier (3A)' },
  { value: '2A', label: 'AC 2-Tier (2A)' },
  { value: '1A', label: 'AC First (1A)' },
]

// Train type options
const TRAIN_TYPES = [
  { value: 'Rajdhani', label: 'Rajdhani' },
  { value: 'Shatabdi', label: 'Shatabdi' },
  { value: 'Express', label: 'Express' },
  { value: 'Superfast', label: 'Superfast' },
  { value: 'Mail', label: 'Mail' },
  { value: 'Passenger', label: 'Passenger' },
]

// Departure time slots
const TIME_SLOTS = [
  { value: 'early_morning', label: 'Early Morning (00:00-06:00)', min: 0, max: 6 },
  { value: 'morning', label: 'Morning (06:00-12:00)', min: 6, max: 12 },
  { value: 'afternoon', label: 'Afternoon (12:00-18:00)', min: 12, max: 18 },
  { value: 'evening', label: 'Evening (18:00-24:00)', min: 18, max: 24 },
]

function TrainResultsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  
  const origin = searchParams.get('origin') || ''
  const destination = searchParams.get('destination') || ''
  const departureDate = searchParams.get('departure_date') || ''
  const initialTrainClass = searchParams.get('train_class') || ''
  const passengers = searchParams.get('passengers') || '1'
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<ErrorType | null>(null)
  const [results, setResults] = useState<TrainSearchResponse | null>(null)
  
  // Sorting
  const [sortBy, setSortBy] = useState<'departure' | 'duration' | 'price'>('departure')
  
  // Filters (matching flight filter experience)
  const [showFilters, setShowFilters] = useState(false)
  const [selectedClasses, setSelectedClasses] = useState<string[]>(initialTrainClass ? [initialTrainClass] : [])
  const [selectedTypes, setSelectedTypes] = useState<string[]>([])
  const [selectedTimeSlots, setSelectedTimeSlots] = useState<string[]>([])
  const [maxPrice, setMaxPrice] = useState<number | null>(null)
  const [maxStops, setMaxStops] = useState<number | null>(null)
  
  useEffect(() => {
    const fetchTrains = async () => {
      if (!origin || !destination || !departureDate) {
        setError('generic')
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
        
        const response = await apiFetch(`/api/search/trains?${params}`)
        
        if (!response.ok) {
          // Log for developers, show friendly error to users
          const errorData = await response.json().catch(() => ({}))
          console.error('[TrainSearch] API Error:', response.status, errorData)
          setError(getErrorType(response.status))
          return
        }
        
        const rawData = await response.json()
        
        // Map the API response to our expected interface
        // Backend returns { status, route: { origin_city, ... }, offers, ... }
        const data: TrainSearchResponse = {
          offers: rawData.offers || [],
          search_id: rawData.search_id,
          cached: rawData.cached || false,
          timestamp: rawData.timestamp,
          origin_city: rawData.route?.origin_city || origin,
          destination_city: rawData.route?.destination_city || destination,
          distance_km: rawData.route?.distance_km || null,
          is_fallback: rawData.is_fallback || false,
          fallback_message: rawData.fallback_message || null,
        }
        
        setResults(data)
        
        // Save to recent searches
        addRecentSearch({
          mode: 'train',
          origin: data.origin_city || origin,
          destination: data.destination_city || destination,
          departureDate,
          passengers: parseInt(passengers),
          trainClass: initialTrainClass || undefined,
        })
        
        // Update price if we have results
        if (data.offers.length > 0 && !data.is_fallback) {
          const lowestPrice = Math.min(...data.offers.map(o => o.avg_price))
          updateRecentSearchPrice('train', origin, destination, departureDate, lowestPrice, 'INR')
        }
        
      } catch (err) {
        console.error('[TrainSearch] Fetch error:', err)
        setError(getErrorType(undefined, err instanceof Error ? err : undefined))
      } finally {
        setLoading(false)
      }
    }
    
    fetchTrains()
  }, [origin, destination, departureDate, passengers, initialTrainClass])
  
  // Filter and sort offers
  const getFilteredAndSortedOffers = () => {
    if (!results?.offers) return []
    
    let filtered = results.offers.filter(offer => {
      // Skip fallback in filtering
      if (offer.is_fallback) return true
      
      // Filter by class
      if (selectedClasses.length > 0) {
        const hasClass = offer.available_classes.some(c => selectedClasses.includes(c.class))
        if (!hasClass) return false
      }
      
      // Filter by train type
      if (selectedTypes.length > 0) {
        const matchesType = selectedTypes.some(type => 
          offer.train_type?.toLowerCase().includes(type.toLowerCase()) ||
          offer.train_name?.toLowerCase().includes(type.toLowerCase())
        )
        if (!matchesType) return false
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
      
      // Filter by stops
      if (maxStops !== null && offer.stops_count > maxStops) return false
      
      return true
    })
    
    // Sort (fallback always at end)
    filtered.sort((a, b) => {
      if (a.is_fallback) return 1
      if (b.is_fallback) return -1
      
      switch (sortBy) {
        case 'departure':
          return new Date(a.departure_time).getTime() - new Date(b.departure_time).getTime()
        case 'duration':
          return a.duration_minutes - b.duration_minutes
        case 'price':
          return a.avg_price - b.avg_price
        default:
          return 0
      }
    })
    
    return filtered
  }
  
  const filteredOffers = getFilteredAndSortedOffers()
  const hasActiveFilters = selectedClasses.length > 0 || selectedTypes.length > 0 || 
                           selectedTimeSlots.length > 0 || maxPrice !== null || maxStops !== null
  
  const clearFilters = () => {
    setSelectedClasses([])
    setSelectedTypes([])
    setSelectedTimeSlots([])
    setMaxPrice(null)
    setMaxStops(null)
  }
  
  const toggleClass = (cls: string) => {
    setSelectedClasses(prev => 
      prev.includes(cls) ? prev.filter(c => c !== cls) : [...prev, cls]
    )
  }
  
  const toggleType = (type: string) => {
    setSelectedTypes(prev => 
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
    }), { min: Infinity, max: 0 }) || { min: 0, max: 10000 }
  
  return (
    <div className="min-h-screen bg-[#FAF9F6]">
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
          
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <Train className="h-6 w-6 text-blue-600" />
                <h1 className="text-2xl font-bold text-gray-900">
                  Trains from {results?.origin_city || origin} to {results?.destination_city || destination}
                </h1>
              </div>
              <p className="text-gray-600">
                {formatDate(departureDate)} • {passengers} passenger{parseInt(passengers) > 1 ? 's' : ''}
              </p>
            </div>
            
            {/* Modify Search + Filter buttons */}
            <div className="flex items-center gap-2">
              <ModifySearchButton 
                service="trains"
                searchParams={{
                  origin_city: origin,
                  destination_city: destination,
                  departure_date: departureDate,
                }}
                variant="default"
              />
            
            {/* Filter toggle button - Only show for actual train results */}
            {results && !results.is_fallback && (
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition ${
                  hasActiveFilters 
                    ? 'border-blue-500 bg-blue-50 text-blue-700' 
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <SlidersHorizontal className="h-4 w-4" />
                Filters
                {hasActiveFilters && (
                  <span className="bg-blue-600 text-white text-xs px-1.5 py-0.5 rounded-full">
                    {selectedClasses.length + selectedTypes.length + selectedTimeSlots.length + (maxPrice ? 1 : 0) + (maxStops !== null ? 1 : 0)}
                  </span>
                )}
              </button>
            )}
            </div>
          </div>
        </div>
        
        {/* Filters Panel - Only for actual train results */}
        {showFilters && results && !results.is_fallback && (
          <div className="bg-white rounded-lg border shadow-sm p-4 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium text-gray-900">Filter Results</h3>
              {hasActiveFilters && (
                <button onClick={clearFilters} className="text-sm text-blue-600 hover:text-blue-800">
                  Clear all
                </button>
              )}
            </div>
            
            <div className="grid md:grid-cols-4 gap-6">
              {/* Train Class */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Class</h4>
                <div className="space-y-2">
                  {TRAIN_CLASSES.map(cls => (
                    <label key={cls.value} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedClasses.includes(cls.value)}
                        onChange={() => toggleClass(cls.value)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-600">{cls.label}</span>
                    </label>
                  ))}
                </div>
              </div>
              
              {/* Train Type */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">Train Type</h4>
                <div className="space-y-2">
                  {TRAIN_TYPES.map(type => (
                    <label key={type.value} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedTypes.includes(type.value)}
                        onChange={() => toggleType(type.value)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-600">{type.label}</span>
                    </label>
                  ))}
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
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-600">{slot.label}</span>
                    </label>
                  ))}
                </div>
              </div>
              
              {/* Price & Stops */}
              <div className="space-y-4">
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
                    className="w-full"
                  />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Max Stops</h4>
                  <select
                    value={maxStops ?? ''}
                    onChange={(e) => setMaxStops(e.target.value ? parseInt(e.target.value) : null)}
                    className="w-full px-3 py-2 border rounded-lg text-sm"
                  >
                    <option value="">Any</option>
                    <option value="0">Non-stop</option>
                    <option value="5">Up to 5 stops</option>
                    <option value="10">Up to 10 stops</option>
                    <option value="15">Up to 15 stops</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Sort Controls - Only for actual train results, not redirects */}
        {!loading && !error && results && !results.is_fallback && filteredOffers.length > 1 && (
          <div className="flex items-center gap-4 mb-6">
            <span className="text-sm text-gray-600">Sort by:</span>
            <div className="flex gap-2">
              {(['departure', 'duration', 'price'] as const).map(option => (
                <button
                  key={option}
                  onClick={() => setSortBy(option)}
                  className={`px-3 py-1 text-sm rounded-full transition ${
                    sortBy === option
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {option === 'departure' ? 'Earliest' : option === 'duration' ? 'Fastest' : 'Cheapest'}
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* Loading State - Service-specific animation */}
        {loading && (
          <TransportLoadingState 
            mode="train"
            origin={results?.origin_city || origin}
            destination={results?.destination_city || destination}
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
        
        {/* No Results State - when search succeeded but truly empty (not fallback) */}
        {!loading && !error && results && results.offers.length === 0 && !results.is_fallback && (
          <NoResultsState
            service="train"
            origin={origin}
            destination={destination}
            date={departureDate}
            onChangeDate={() => router.push(`/?tab=trains&origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}`)}
            onModifySearch={() => router.push('/?tab=trains')}
            onGoBack={() => router.push('/')}
          />
        )}
        
        {/* Results */}
        {!loading && !error && results && (results.offers.length > 0 || results.is_fallback) && (
          <>
            {/* REDIRECT-ONLY: Show clean redirect card, NOT warnings */}
            {results.is_fallback ? (
              <TrainRedirectCard
                originCity={results.origin_city || origin}
                destinationCity={results.destination_city || destination}
                distanceKm={results.distance_km}
                estimatedFares={results.offers[0]?.available_classes || []}
                bookingPartners={results.offers[0]?.booking_partners || []}
                departureDate={departureDate}
              />
            ) : (
              <>
                {/* Results Count - Only for actual train results */}
                <p className="text-sm text-gray-600 mb-4">
                  {filteredOffers.length} train{filteredOffers.length !== 1 ? 's' : ''} found
                  {results.distance_km && ` • ${results.distance_km} km`}
                  {hasActiveFilters && results.offers.length !== filteredOffers.length && (
                    <span className="text-blue-600"> (filtered from {results.offers.length})</span>
                  )}
                </p>
                
                {/* No results after filter */}
                {filteredOffers.length === 0 && hasActiveFilters && (
                  <div className="text-center py-8 bg-white rounded-lg border">
                    <Filter className="h-8 w-8 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-600">No trains match your filters</p>
                    <button 
                      onClick={clearFilters}
                      className="mt-2 text-blue-600 hover:text-blue-800 text-sm"
                    >
                      Clear filters
                    </button>
                  </div>
                )}
                
                {/* Train Cards */}
                <div className="space-y-4">
                  {filteredOffers.map((offer, idx) => (
                    <TrainCard key={offer.offer_id} offer={offer} index={idx} departureDate={departureDate} />
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default function TrainResultsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    }>
      <TrainResultsContent />
    </Suspense>
  )
}
