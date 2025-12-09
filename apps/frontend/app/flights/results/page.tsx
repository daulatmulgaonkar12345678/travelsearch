'use client'

import { useEffect, useState, Suspense } from 'react'
import React from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import TrustStrip from '@/components/layout/TrustStrip'
import EnhancedFlightCard from '@/components/results/EnhancedFlightCard'
import SortTabs from '@/components/results/SortTabs'
import ImprovedFilters from '@/components/results/ImprovedFilters'
import FlexibleDateBar from '@/components/results/FlexibleDateBar'
import MonthView from '@/components/results/MonthView'
import FlightLoadingState from '@/components/loading/FlightLoadingState'
import { FlightOffer } from '@/components/results/ResultCard'
import { Loader2 } from 'lucide-react'
import { API_ENDPOINTS, apiFetch } from '@/lib/config'

function SearchResultsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [offers, setOffers] = useState<FlightOffer[]>([])
  const [filteredOffers, setFilteredOffers] = useState<FlightOffer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sortType, setSortType] = useState<'best' | 'cheapest' | 'fastest'>('best')

  // Flexible dates state
  const [dateOptions, setDateOptions] = useState<any[]>([])
  const [selectedDate, setSelectedDate] = useState(searchParams.get('departure_date') || '')
  const [datePriceCache, setDatePriceCache] = useState<Map<string, number>>(new Map())
  
  // Month View state
  const [showMonthView, setShowMonthView] = useState(false)

  // Filter state
  const [filters, setFilters] = useState({
    stops: [] as string[],
    departureTimeRange: [0, 23] as [number, number],
    durationRange: [0, 1440] as [number, number],
    airlines: [] as string[],
  })

  // Search parameters
  const origin = searchParams.get('origin') || ''
  const destination = searchParams.get('destination') || ''
  const tripType = searchParams.get('trip_type') || 'oneway'
  const returnDate = searchParams.get('return_date') || ''
  const cabinClass = searchParams.get('cabin_class') || 'economy'

  // Fetch real per-day prices for date strip
  const fetchDateRangePrices = async (centerDate: string) => {
    try {
      const center = new Date(centerDate)
      const dates = []
      
      // Generate date range (-3 to +3 days)
      for (let i = -3; i <= 3; i++) {
        const date = new Date(center)
        date.setDate(center.getDate() + i)
        dates.push(date.toISOString().split('T')[0])
      }
      
      const adults = parseInt(searchParams.get('adults') || '1', 10)
      const children = parseInt(searchParams.get('children') || '0', 10)
      const infants = parseInt(searchParams.get('infants') || '0', 10)
      
      const response = await apiFetch(API_ENDPOINTS.pricingDateRange, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin,
          destination,
          dates,
          adults,
          children,
          infants,
          cabin_class: cabinClass,
          trip_type: tripType
        })
      })
      
      if (response.ok) {
        const datePrices = await response.json()
        const newCache = new Map<string, number>()
        
        datePrices.forEach((dp: any) => {
          if (dp.min_price !== null && dp.min_price !== undefined) {
            newCache.set(dp.date, dp.min_price)
          }
        })
        
        setDatePriceCache(newCache)
      } else {
        console.error('Failed to fetch date range prices:', response.status)
      }
    } catch (error) {
      console.error('Error fetching date range prices:', error)
    }
  }

  // Fetch prices for entire month (for Month View)
  const fetchPricesForMonth = async (month: string): Promise<Array<{date: string, price: number | null, isAvailable: boolean}>> => {
    try {
      const [year, monthNum] = month.split('-').map(Number)
      const daysInMonth = new Date(year, monthNum, 0).getDate()
      const dates: string[] = []
      
      for (let day = 1; day <= daysInMonth; day++) {
        dates.push(`${year}-${String(monthNum).padStart(2, '0')}-${String(day).padStart(2, '0')}`)
      }
      
      const adults = parseInt(searchParams.get('adults') || '1', 10)
      const children = parseInt(searchParams.get('children') || '0', 10)
      const infants = parseInt(searchParams.get('infants') || '0', 10)
      
      const response = await apiFetch(API_ENDPOINTS.pricingDateRange, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          origin,
          destination,
          dates,
          adults,
          children,
          infants,
          cabin_class: cabinClass,
          trip_type: tripType
        })
      })
      
      if (response.ok) {
        const datePrices = await response.json()
        
        // Update cache with these prices
        const newCache = new Map(datePriceCache)
        datePrices.forEach((dp: any) => {
          if (dp.min_price !== null) {
            newCache.set(dp.date, dp.min_price)
          }
        })
        setDatePriceCache(newCache)
        
        // Return formatted data for MonthView
        return datePrices.map((dp: any) => ({
          date: dp.date,
          price: dp.min_price,
          isAvailable: dp.min_price !== null
        }))
      }
      
      return []
    } catch (error) {
      console.error('Error fetching month prices:', error)
      return []
    }
  }

  // Initialize flexible date bar and fetch prices
  useEffect(() => {
    if (selectedDate && origin && destination) {
      // Fetch real prices for visible dates
      fetchDateRangePrices(selectedDate)
    }
  }, [selectedDate, origin, destination, cabinClass, tripType])

  // Generate date options from cache
  useEffect(() => {
    if (selectedDate) {
      const dates = generateDateOptions(selectedDate)
      setDateOptions(dates)
    }
  }, [selectedDate, datePriceCache])

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
        currency: 'INR',
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
        setDatePriceCache((prev) => {
          const newCache = new Map(prev)
          newCache.set(selectedDate, minPrice)
          return newCache
        })
      }

      // Initialize filters based on available data
      if (fetchedOffers.length > 0) {
        const durations = fetchedOffers.map((o: FlightOffer) => o.total_duration_minutes || 0)
        const uniqueAirlines = Array.from(
          new Set(fetchedOffers.flatMap((o: FlightOffer) => o.segments.map((s) => s.carrier_name)))
        ).sort()

        setFilters((prev) => ({
          ...prev,
          durationRange: [Math.min(...durations), Math.max(...durations)],
          airlines: uniqueAirlines,
        }))
      }
    } catch (err) {
      console.error('Search error:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch results')
    } finally {
      setLoading(false)
    }
  }

  // Calculate tab prices (Best/Cheapest/Fastest)
  const tabPrices = React.useMemo(() => {
    if (filteredOffers.length === 0) {
      return { best: undefined, cheapest: undefined, fastest: undefined }
    }

    // Cheapest: minimum price
    const cheapestPrice = Math.min(...filteredOffers.map(o => o.price))

    // Fastest: price of the flight with minimum duration
    const fastestFlight = filteredOffers.reduce((min, offer) => 
      (offer.total_duration_minutes || 0) < (min.total_duration_minutes || 0) ? offer : min
    )
    const fastestPrice = fastestFlight.price

    // Best: price of the first flight when sorted by "best" logic
    const bestSorted = [...filteredOffers].sort((a, b) => {
      const scoreA = a.price / 1000 + (a.total_duration_minutes || 0) / 60
      const scoreB = b.price / 1000 + (b.total_duration_minutes || 0) / 60
      return scoreA - scoreB
    })
    const bestPrice = bestSorted[0]?.price

    return { best: bestPrice, cheapest: cheapestPrice, fastest: fastestPrice }
  }, [filteredOffers])

  // Apply filters and sorting
  useEffect(() => {
    let filtered = [...offers]

    // Filter by stops
    if (filters.stops.length > 0) {
      filtered = filtered.filter((offer) => {
        if (filters.stops.includes('Direct') && offer.stops === 0) return true
        if (filters.stops.includes('1 stop') && offer.stops === 1) return true
        if (filters.stops.includes('2+ stops') && offer.stops >= 2) return true
        return false
      })
    }

    // Filter by departure time
    filtered = filtered.filter((offer) => {
      const depTime = new Date(offer.segments[0].departure_time).getHours()
      return depTime >= filters.departureTimeRange[0] && depTime <= filters.departureTimeRange[1]
    })

    // Filter by duration
    filtered = filtered.filter((offer) => {
      const duration = offer.total_duration_minutes || 0
      return duration >= filters.durationRange[0] && duration <= filters.durationRange[1]
    })

    // Filter by airlines
    if (filters.airlines.length > 0) {
      filtered = filtered.filter((offer) => {
        return offer.segments.some((seg) => filters.airlines.includes(seg.carrier_name))
      })
    }

    // Sort
    if (sortType === 'cheapest') {
      filtered.sort((a, b) => a.price - b.price)
    } else if (sortType === 'fastest') {
      filtered.sort((a, b) => (a.total_duration_minutes || 0) - (b.total_duration_minutes || 0))
    } else {
      // Best: weighted combination
      filtered.sort((a, b) => {
        const scoreA = a.price / 1000 + (a.total_duration_minutes || 0) / 60
        const scoreB = b.price / 1000 + (b.total_duration_minutes || 0) / 60
        return scoreA - scoreB
      })
    }

    setFilteredOffers(filtered)
  }, [offers, filters, sortType])

  const handleDateSelect = async (newDate: string) => {
    setSelectedDate(newDate)

    const newParams = new URLSearchParams(searchParams.toString())
    newParams.set('departure_date', newDate)
    router.push(`/flights/results?${newParams.toString()}`, { scroll: false })
  }

  const handleResetFilters = () => {
    const durations = offers.map((o) => o.total_duration_minutes || 0)
    const uniqueAirlines = Array.from(
      new Set(offers.flatMap((o) => o.segments.map((s) => s.carrier_name)))
    ).sort()

    setFilters({
      stops: [],
      departureTimeRange: [0, 23],
      durationRange: [Math.min(...durations), Math.max(...durations)],
      airlines: uniqueAirlines,
    })
  }

  const minDuration = Math.min(...offers.map((o) => o.total_duration_minutes || 0))
  const maxDuration = Math.max(...offers.map((o) => o.total_duration_minutes || 0))

  // Assign badges to top offers
  const getOfferWithBadge = (offer: FlightOffer, index: number) => {
    if (sortType === 'cheapest' && index === 0) return 'cheapest'
    if (sortType === 'fastest' && index === 0) return 'fastest'
    if (sortType === 'best' && index === 0) return 'best'
    return undefined
  }

  if (loading && offers.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">
            Searching flights from {origin} to {destination}...
          </p>
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
      <TrustStrip />

      {/* Flexible Date Bar */}
      {dateOptions.length > 0 && (
        <FlexibleDateBar
          dates={dateOptions}
          selectedDate={selectedDate}
          onDateSelect={handleDateSelect}
          loading={loading}
          onMonthViewClick={() => setShowMonthView(true)}
        />
      )}
      
      {/* Month View Modal */}
      <MonthView
        isOpen={showMonthView}
        onClose={() => setShowMonthView(false)}
        selectedDate={selectedDate}
        onDateSelect={handleDateSelect}
        origin={origin}
        destination={destination}
        fetchPricesForMonth={fetchPricesForMonth}
      />

      {/* Sort Tabs */}
      <SortTabs
        activeSort={sortType}
        onSortChange={setSortType}
        prices={tabPrices}
        currency="INR"
      />

      <div className="container mx-auto px-4 py-4">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Filters Sidebar */}
          <div className="lg:col-span-1">
            <div className="lg:sticky lg:top-24">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
                <button
                  onClick={handleResetFilters}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  Reset all
                </button>
              </div>
              <ImprovedFilters
                filters={filters}
                onFilterChange={setFilters}
                offers={offers}
                filteredOffers={filteredOffers}
                minDuration={minDuration}
                maxDuration={maxDuration}
              />
            </div>
          </div>

          {/* Results */}
          <div className="lg:col-span-3">
            <div className="mb-4">
              <p className="text-gray-600 text-sm">
                {filteredOffers.length === offers.length
                  ? `${offers.length} flight${offers.length !== 1 ? 's' : ''} found`
                  : `${filteredOffers.length} of ${offers.length} flights`}
              </p>
            </div>

            <div className="space-y-4">
              {filteredOffers.map((offer, index) => (
                <EnhancedFlightCard
                  key={offer.offer_id}
                  offer={offer}
                  badge={getOfferWithBadge(offer, index)}
                  searchParams={searchParams}
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
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-screen">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
        </div>
      }
    >
      <SearchResultsContent />
    </Suspense>
  )
}
