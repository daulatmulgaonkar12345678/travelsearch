'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import ResultCard, { FlightOffer } from '@/components/results/ResultCard'
import SortTabs from '@/components/results/SortTabs'
import AdvancedFilters from '@/components/results/AdvancedFilters'
import FlexibleDateBar from '@/components/results/FlexibleDateBar'
import { Loader2, SlidersHorizontal, X } from 'lucide-react'
import { API_ENDPOINTS, apiFetch } from '@/lib/config'

function SearchResultsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [offers, setOffers] = useState<FlightOffer[]>([])
  const [filteredOffers, setFilteredOffers] = useState<FlightOffer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [sortType, setSortType] = useState<'best' | 'cheapest' | 'fastest'>('best')

  // Flexible dates state
  const [dateOptions, setDateOptions] = useState<any[]>([])
  const [selectedDate, setSelectedDate] = useState(searchParams.get('departure_date') || '')
  const [datePriceCache, setDatePriceCache] = useState<Map<string, number>>(new Map())

  // Filter state
  const [filters, setFilters] = useState({
    stops: [] as string[],
    departureTimeRange: [0, 23] as [number, number],
    durationRange: [0, 1440] as [number, number], // minutes
    airlines: [] as string[],
  })

  // Search parameters
  const origin = searchParams.get('origin') || ''
  const destination = searchParams.get('destination') || ''
  const tripType = searchParams.get('trip_type') || 'oneway'
  const returnDate = searchParams.get('return_date') || ''
  const cabinClass = searchParams.get('cabin_class') || 'economy'

  // Initialize flexible date bar
  useEffect(() => {
    if (selectedDate) {
      const dates = generateDateOptions(selectedDate)
      setDateOptions(dates)
    }
  }, [selectedDate])

  const generateDateOptions = (centerDate: string) => {
    const center = new Date(centerDate)
    const options = []

    for (let i = -3; i <= 3; i++) {
      const date = new Date(center)
      date.setDate(center.getDate() + i)
      
      const dateStr = date.toISOString().split('T')[0]
      options.push({
        date: dateStr,
        dayName: date.toLocaleDateString('en-US', { weekday: 'short' }),
        dayNum: date.getDate().toString(),
        month: date.toLocaleDateString('en-US', { month: 'short' }),
        bestPrice: datePriceCache.get(dateStr) || null,
        currency: 'INR'
      })
    }

    return options
  }

  useEffect(() => {
    if (!origin || !destination || !selectedDate) {
      setError('Missing required search parameters')
      setLoading(false)
      return
    }

    fetchResults()
  }, [origin, destination, selectedDate, tripType, returnDate, cabinClass])

  const fetchResults = async () => {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams({
        origin,
        destination,
        departure_date: selectedDate,
        trip_type: tripType,
        adults: searchParams.get('adults') || '1',
        children: searchParams.get('children') || '0',
        infants: searchParams.get('infants') || '0',
        cabin_class: cabinClass,
      })

      if (returnDate && tripType === 'roundtrip') {
        params.set('return_date', returnDate)
      }

      const url = `${API_ENDPOINTS.searchFlights}?${params}`
      const response = await apiFetch(url)

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      const fetchedOffers = data.offers || []
      setOffers(fetchedOffers)

      // Cache minimum price for this date
      if (fetchedOffers.length > 0) {
        const minPrice = Math.min(...fetchedOffers.map((o: FlightOffer) => o.price))
        setDatePriceCache(prev => new Map(prev).set(selectedDate, minPrice))
      }

      // Initialize filters based on available data
      if (fetchedOffers.length > 0) {
        const durations = fetchedOffers.map((o: FlightOffer) => o.total_duration_minutes || 0)
        const uniqueAirlines = Array.from(new Set(
          fetchedOffers.flatMap((o: FlightOffer) => 
            o.segments.map(s => s.carrier_name)
          )
        )).sort()

        setFilters(prev => ({
          ...prev,
          durationRange: [Math.min(...durations), Math.max(...durations)],
          airlines: uniqueAirlines
        }))
      }
    } catch (err) {
      console.error('Search error:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch results')
    } finally {
      setLoading(false)
    }
  }

  // Apply filters and sorting
  useEffect(() => {
    let filtered = [...offers]

    // Filter by stops
    if (filters.stops.length > 0) {
      filtered = filtered.filter(offer => {
        if (filters.stops.includes('Direct') && offer.stops === 0) return true
        if (filters.stops.includes('1 stop') && offer.stops === 1) return true
        if (filters.stops.includes('2+ stops') && offer.stops >= 2) return true
        return false
      })
    }

    // Filter by departure time
    filtered = filtered.filter(offer => {
      const depTime = new Date(offer.segments[0].departure_time).getHours()
      return depTime >= filters.departureTimeRange[0] && depTime <= filters.departureTimeRange[1]
    })

    // Filter by duration
    filtered = filtered.filter(offer => {
      const duration = offer.total_duration_minutes || 0
      return duration >= filters.durationRange[0] && duration <= filters.durationRange[1]
    })

    // Filter by airlines
    if (filters.airlines.length > 0) {
      filtered = filtered.filter(offer => {
        return offer.segments.some(seg => filters.airlines.includes(seg.carrier_name))
      })
    }

    // Sort
    if (sortType === 'cheapest') {
      filtered.sort((a, b) => a.price - b.price)
    } else if (sortType === 'fastest') {
      filtered.sort((a, b) => (a.total_duration_minutes || 0) - (b.total_duration_minutes || 0))
    } else {
      // Best: simple heuristic (can be improved)
      filtered.sort((a, b) => {
        const scoreA = a.price / 1000 + (a.total_duration_minutes || 0) / 60
        const scoreB = b.price / 1000 + (b.total_duration_minutes || 0) / 60
        return scoreA - scoreB
      })
    }

    setFilteredOffers(filtered)
  }, [offers, filters, sortType])

  const handleProviderSelect = (provider: any, offer: FlightOffer) => {
    const firstSegment = offer.segments[0]
    const lastSegment = offer.segments[offer.segments.length - 1]

    const params = new URLSearchParams({
      origin: firstSegment.departure_airport,
      destination: lastSegment.arrival_airport,
      departure_date: new Date(firstSegment.departure_time).toISOString().split('T')[0],
      departure_time: new Date(firstSegment.departure_time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
      arrival_time: new Date(lastSegment.arrival_time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
      airline: firstSegment.carrier_name,
      flight_number: firstSegment.flight_number || '',
      price: offer.price.toString(),
      currency: offer.currency,
      stops: offer.stops.toString(),
      adults: searchParams.get('adults') || '1',
      children: searchParams.get('children') || '0',
      infants: searchParams.get('infants') || '0',
      cabin_class: offer.cabin_class || 'economy',
    })

    if (returnDate) {
      params.set('return_date', returnDate)
    }

    router.push(`/flights/vendors?${params.toString()}`)
  }

  const handleDateSelect = async (newDate: string) => {
    setSelectedDate(newDate)
    
    // Update URL
    const newParams = new URLSearchParams(searchParams.toString())
    newParams.set('departure_date', newDate)
    router.push(`/flights/results?${newParams.toString()}`, { scroll: false })
  }

  const handleResetFilters = () => {
    const durations = offers.map(o => o.total_duration_minutes || 0)
    const uniqueAirlines = Array.from(new Set(
      offers.flatMap(o => o.segments.map(s => s.carrier_name))
    )).sort()

    setFilters({
      stops: [],
      departureTimeRange: [0, 23],
      durationRange: [Math.min(...durations), Math.max(...durations)],
      airlines: uniqueAirlines
    })
  }

  const availableAirlines = Array.from(new Set(
    offers.flatMap(o => o.segments.map(s => s.carrier_name))
  )).sort()

  const minDuration = Math.min(...offers.map(o => o.total_duration_minutes || 0))
  const maxDuration = Math.max(...offers.map(o => o.total_duration_minutes || 0))

  if (loading && offers.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Searching flights from {origin} to {destination}...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-red-900 mb-2">Search Error</h3>
          <p className="text-red-700">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="mt-4 px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Back to Search
          </button>
        </div>
      </div>
    )
  }

  if (offers.length === 0) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">No flights found</h3>
        <p className="text-gray-600 mb-4">
          We couldn't find any flights from {origin} to {destination} on {selectedDate}.
        </p>
        <button
          onClick={() => router.push('/')}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Try Another Search
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      {/* Flexible Date Bar */}
      {dateOptions.length > 0 && (
        <FlexibleDateBar
          dates={dateOptions}
          selectedDate={selectedDate}
          onDateSelect={handleDateSelect}
          loading={loading}
        />
      )}

      {/* Sort Tabs */}
      <SortTabs
        activeSort={sortType}
        onSortChange={setSortType}
        counts={{
          best: filteredOffers.length,
          cheapest: filteredOffers.length,
          fastest: filteredOffers.length
        }}
      />

      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Filters Sidebar */}
          <div className="lg:col-span-1">
            <div className="sticky top-32">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
                <button
                  onClick={handleResetFilters}
                  className="text-sm text-blue-600 hover:text-blue-700 flex items-center space-x-1"
                >
                  <X className="h-4 w-4" />
                  <span>Reset</span>
                </button>
              </div>
              <AdvancedFilters
                filters={filters}
                onFilterChange={setFilters}
                availableAirlines={availableAirlines}
                minDuration={minDuration}
                maxDuration={maxDuration}
              />
            </div>
          </div>

          {/* Results */}
          <div className="lg:col-span-3">
            <div className="mb-4 flex items-center justify-between">
              <p className="text-gray-600">
                {filteredOffers.length} of {offers.length} flights
                {filteredOffers.length !== offers.length && ' (filtered)'}
              </p>
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="lg:hidden flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                <SlidersHorizontal className="h-4 w-4" />
                <span>Filters</span>
              </button>
            </div>

            <div className="space-y-4">
              {filteredOffers.map((offer) => (
                <ResultCard
                  key={offer.offer_id}
                  offer={offer}
                  badge={undefined}
                  onProviderSelect={handleProviderSelect}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function SearchResultsPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
      </div>
    }>
      <SearchResultsContent />
    </Suspense>
  )
}
