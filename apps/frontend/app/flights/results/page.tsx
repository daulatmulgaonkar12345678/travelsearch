'use client'

import { useEffect, useState, Suspense, useRef, useMemo } from 'react'
						 
import { useSearchParams, useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import EnhancedFlightCard from '@/components/results/EnhancedFlightCard'
import SortTabs from '@/components/results/SortTabs'
import ImprovedFilters from '@/components/results/ImprovedFilters'
import FlexibleDateBar from '@/components/results/FlexibleDateBar'
import MonthView from '@/components/results/MonthView'
import FlightLoadingState from '@/components/loading/FlightLoadingState'
import ServiceUnavailable from '@/components/common/ServiceUnavailable'
import { FlightOffer } from '@/components/results/ResultCard'
import { Loader2, RefreshCw } from 'lucide-react'
import { apiFetch } from '@/lib/api'
import { requestCache } from '@/lib/requestCache'
import { runFallbackSearches, type FallbackSuggestions } from '@/lib/fallbackSearch'
import NoFlightsWithSuggestions from '@/components/results/NoFlightsWithSuggestions'
// Phase 2 Trust & Feature Components
import TrustIndicators from '@/components/trust/TrustIndicators'
import { PriceComparisonNotice, PlatformExplanation } from '@/components/trust/Microcopy'
import SaveSearchButton from '@/components/features/SaveSearchButton'
import TrackPrice from '@/components/features/TrackPrice'
// Cost-controlled search source indicator
import PriceSourceBadge from '@/components/results/PriceSourceBadge'
// Recent search store - automatic localStorage persistence
import { addRecentSearch, updateRecentSearchPrice } from '@/lib/recentSearchStore'

interface DateOption {
  date: string
  dayName: string
  dayNum: string
  month: string
  bestPrice: number | null
  currency: string
}

const isValidAirportCode = (value: string) =>
  typeof value === 'string' &&
  value.length === 3 &&
  value === value.toUpperCase()

  
function SearchResultsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()

  // 🔹 Search parameters FIRST
  const origin = searchParams.get('origin') || ''
  const destination = searchParams.get('destination') || ''
  const tripType = searchParams.get('trip_type') || 'oneway'
  const returnDate = searchParams.get('return_date') || ''
  const cabinClass = searchParams.get('cabin_class') || 'economy'
  const includeNearbyOrigin = searchParams.get('include_nearby_origin') === 'true'
  const includeNearbyDestination = searchParams.get('include_nearby_destination') === 'true'

  // ========================================
  // 🔒 FINAL SAFETY CHECK - BLOCK INVALID AIRPORTS
  // ========================================
  const [validationError, setValidationError] = useState<string | null>(null)
  
  useEffect(() => {
    // Validate airports before any API calls
    if (!origin || !destination) {
      setValidationError('Missing airport information. Please select airports from the search page.')
      setTimeout(() => router.push('/'), 3000)
      return
    }

    // Validate IATA format (must be exactly 3 uppercase letters)
    const iataRegex = /^[A-Z]{3}$/
    if (!iataRegex.test(origin) || !iataRegex.test(destination)) {
      setValidationError('Invalid airport codes detected. Redirecting to search page...')
      setTimeout(() => router.push('/'), 3000)
      return
    }

    // Validate airports are different
    if (origin === destination) {
      setValidationError('Departure and arrival airports must be different. Redirecting to search page...')
      setTimeout(() => router.push('/'), 3000)
      return
    }

    // Validation passed - proceed with search
    setValidationError(null)
  }, [origin, destination, router])

  // Show validation error screen if invalid
  if (validationError) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="max-w-2xl mx-auto px-4 py-16">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
            <div className="flex justify-center mb-4">
              <svg className="h-16 w-16 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-3">Invalid Search</h2>
            <p className="text-gray-700 mb-6">{validationError}</p>
            <button
              onClick={() => router.push('/')}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Go to Search Page
            </button>
          </div>
        </div>
      </div>
    )
  }

  // 🔹 State that depends on search params
  const [selectedDate, setSelectedDate] = useState(
    searchParams.get('departure_date') || ''
  )

  // 🔹 NOW validation is safe
  const isSearchValid =
    isValidAirportCode(origin) &&
    isValidAirportCode(destination) &&
    Boolean(selectedDate)

  // 🔹 Other state AFTER validation
  const [offers, setOffers] = useState<FlightOffer[]>([])
  const [filteredOffers, setFilteredOffers] = useState<FlightOffer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [serviceUnavailable, setServiceUnavailable] = useState(false)
  const [sortType, setSortType] =
    useState<'best' | 'cheapest' | 'fastest'>('best')

  const [loadingTimeout, setLoadingTimeout] = useState(false)
  const [showRetry, setShowRetry] = useState(false)
  
  // Fallback suggestions state
  const [fallbackSuggestions, setFallbackSuggestions] = useState<FallbackSuggestions | null>(null)
  const [loadingFallback, setLoadingFallback] = useState(false)
  const [showingFallbackResults, setShowingFallbackResults] = useState(false)
  
  // Cost-controlled search state - tracks if results are from live API or cache
  const [searchSource, setSearchSource] = useState<'AMADEUS' | 'CACHE' | null>(null)
  const [isLiveResults, setIsLiveResults] = useState<boolean>(true)
  const [cacheMessage, setCacheMessage] = useState<string | null>(null)
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null)
  
  // Abort controller ref for cancelling requests
  const abortControllerRef = useRef<AbortController | null>(null)

  // Flexible dates state
  const [dateOptions, setDateOptions] = useState<DateOption[]>([])
																							
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
      
      const response = await apiFetch('/api/pricing/date-range', {
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
      }, {
        timeoutMs: 15000,  // 15 second timeout for pricing (makes multiple API calls)
        maxRetries: 1      // Only 1 retry for pricing to avoid long waits
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
      
      const response = await apiFetch('/api/pricing/date-range', {
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
      }, {
        timeoutMs: 15000,  // 15 second timeout for pricing (makes multiple API calls)
        maxRetries: 1      // Only 1 retry for pricing to avoid long waits
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
    if (selectedDate) {
      const dates = generateDateOptions(selectedDate)
      setDateOptions(dates)
    }
  }, [selectedDate, datePriceCache])  

 
useEffect(() => {
  if (!isSearchValid) {
    setOffers([])
    setFilteredOffers([])
    setLoading(false)
    return
  }

  if (abortControllerRef.current) {
    abortControllerRef.current.abort()
  }

  fetchResults()

  return () => abortControllerRef.current?.abort()
}, [
  origin,
  destination,
  selectedDate,
  tripType,
  returnDate,
  cabinClass,
  includeNearbyOrigin,
  includeNearbyDestination,
])

  const fetchResults = async () => {
    try {
      setLoading(true)
      setError(null)
      setLoadingTimeout(false)
      setShowRetry(false)

      // Create search params object for cache
      const searchParamsObj = {
        origin,
        destination,
        departure_date: selectedDate,
        trip_type: tripType,
        adults: searchParams.get('adults') || '1',
        children: searchParams.get('children') || '0',
        infants: searchParams.get('infants') || '0',
        cabin_class: cabinClass,
        ...(returnDate && tripType === 'roundtrip' && { return_date: returnDate }),
        ...(includeNearbyOrigin && { include_nearby_origin: 'true' }),
        ...(includeNearbyDestination && { include_nearby_destination: 'true' })
      }

      // Check cache first
      const cached = requestCache.get<any>('flights', searchParamsObj)
      if (cached) {
        console.log('[Flights] Using cached data')
        const fetchedOffers = cached.offers || []
        setOffers(fetchedOffers)
        processFlightData(fetchedOffers)
        setLoading(false)
        return
      }

      // Create new abort controller for this request
      const controller = new AbortController()
      abortControllerRef.current = controller

      // Set up loading timeouts
      const timeout8s = setTimeout(() => {
        if (loading) {
          setLoadingTimeout(true)
        }
      }, 8000)

      const timeout12s = setTimeout(() => {
        if (loading) {
          setShowRetry(true)
        }
      }, 12000)

      // Build API path with cache-busting
      const params = new URLSearchParams(searchParamsObj as any)
      // Add cache-busting params
      params.set('request_id', crypto.randomUUID())
      params.set('ts', Date.now().toString())
      const apiPath = `/api/search/flights?${params}`

      // Fetch with abort signal using robust apiFetch and cache: 'no-store'
      // CRITICAL: Add x-search-intent: "real" header to trigger actual API call
      // This is required for cost-controlled Amadeus integration
      const response = await apiFetch(apiPath, {
        signal: controller.signal,
        cache: 'no-store',
        headers: {
          'x-search-intent': 'real'  // Signals explicit user search action
        }
      })

      // Clear timeouts on success
      clearTimeout(timeout8s)
      clearTimeout(timeout12s)

      // Check for 503 Service Unavailable
      if (response.status === 503) {
        const errorData = await response.json()
        console.log('Service unavailable:', errorData)
        setServiceUnavailable(true)
        setLoading(false)
        return
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      const fetchedOffers = data.offers || []

      // Log orchestrator response with fallback details
      console.log('═══════════════════════════════════════════════')
      console.log('🔍 ORCHESTRATOR RESPONSE')
      console.log('═══════════════════════════════════════════════')
      console.log('Status:', data.status)
      console.log('Outcome:', data.outcome)
      console.log('Flights found:', fetchedOffers.length)
      
      // Defensive fallback for total_calls
      if (data.total_calls === undefined || data.total_calls === null) {
        console.warn('⚠️  WARNING: total_calls field missing from orchestrator response!')
        console.log('Total API calls: N/A (field missing)')
      } else {
        console.log('Total API calls:', data.total_calls)
      }
      
      // Log call_records if available
      if (data.call_records && Array.isArray(data.call_records)) {
        console.log('Call records:', data.call_records.length, 'entries')
        data.call_records.forEach((record: any, idx: number) => {
          console.log(`  ${idx + 1}. ${record.supplier}: ${record.status} (${record.latency_ms || 0}ms, ${record.results || 0} results)`)
        })
      }
      
      console.log('Time elapsed:', data.elapsed_seconds?.toFixed(2) + 's')
      
      // Show warnings if any
      if (data.warnings && data.warnings.length > 0) {
        console.log('\n⚠️ WARNINGS:')
        data.warnings.forEach((warn: any) => {
          console.log(`  ${warn.supplier.toUpperCase()}: ${warn.status} - ${warn.reason}`)
          console.log(`  Message: ${warn.message}`)
          if (warn.opened_until) {
            console.log(`  Will retry after: ${warn.opened_until}`)
          }
        })
      }
      
      // Show fallback logs if available
      if (data.logs && data.logs.length > 0) {
        console.log('\n📋 FALLBACK ATTEMPTS:')
        data.logs.forEach((log: any, index: number) => {
          if (log.step === 'primary') {
            console.log(`  ${index + 1}. ✈️  PRIMARY SEARCH: ${log.results || 0} results (${log.latency_ms?.toFixed(0)}ms)`)
          } else if (log.step === 'date_fallback') {
            console.log(`  ${index + 1}. 📅 DATE FALLBACK (${log.date}): ${log.status} - ${log.results || 0} results`)
          } else if (log.step === 'nearby_airports') {
            console.log(`  ${index + 1}. 🗺️  NEARBY AIRPORTS: ${log.status} - ${log.results || 0} results`)
          } else if (log.step === 'hub_composition') {
            console.log(`  ${index + 1}. 🔄 HUB COMPOSITION: ${log.status} - ${log.results || 0} results (${log.latency_ms?.toFixed(0)}ms)`)
          }
        })
      }
      
      // Show suggestions if no results
      if (data.suggestions && data.suggestions.length > 0) {
        console.log('\n💡 SUGGESTIONS:')
        data.suggestions.forEach((sug: any, index: number) => {
          console.log(`  ${index + 1}. ${sug.type.toUpperCase()}: ${sug.description}`)
        })
      }
      
      console.log('═══════════════════════════════════════════════\n')

      // Cache the response
      requestCache.set('flights', searchParamsObj, data)
      
      // Track source metadata for cost-controlled search display
      // source: "AMADEUS" (live) or "CACHE" (cached)
      setSearchSource(data.source || null)
      setIsLiveResults(data.is_live ?? true)
      setCacheMessage(data.cache_message || null)
      setLastUpdatedAt(data.timestamp_display || data.last_live_updated_at || null)
      
      // Check if results are from fallback (backend nearby airport expansion or hub composition)
      const hasFallbackResults = fetchedOffers.some((offer: FlightOffer) => 
        offer.nearby_origin || offer.nearby_destination || offer.composed_via_hub
      )
      setShowingFallbackResults(hasFallbackResults)

      setOffers(fetchedOffers)
      processFlightData(fetchedOffers)
      
      // ===============================================================
      // AUTOMATIC RECENT SEARCH STORAGE
      // Store this search in localStorage after successful API response
      // This happens automatically - no user action required
      // ===============================================================
      try {
        const minPrice = fetchedOffers.length > 0 
          ? Math.min(...fetchedOffers.map(o => o.price || Infinity))
          : undefined
        const currency = fetchedOffers[0]?.currency || 'INR'
        
        addRecentSearch({
          origin: searchParamsObj.origin,
          destination: searchParamsObj.destination,
          departureDate: searchParamsObj.departure_date,
          returnDate: searchParamsObj.return_date,
          adults: parseInt(searchParamsObj.adults || '1'),
          cabinClass: searchParamsObj.cabin_class || 'economy',
          tripType: searchParamsObj.trip_type || 'oneway',
          lastKnownPrice: minPrice,
          lastKnownCurrency: currency,
        })
        console.log('[RecentSearch] Automatically saved search to localStorage')
      } catch (recentSearchErr) {
        // Non-critical - don't fail the search if this fails
        console.warn('[RecentSearch] Failed to save recent search:', recentSearchErr)
      }
      
      // IMPORTANT: Do NOT trigger client-side fallback if orchestrator already ran all fallbacks
      // The orchestrator response includes status="completed" and outcome="no_results" when all fallbacks are exhausted
      if (fetchedOffers.length === 0 && data.outcome !== 'no_results') {
        console.log('[Flights] 0 results - checking if client-side fallback needed')
        // Only trigger client fallback if orchestrator didn't run (backward compatibility)
        if (!data.outcome) {
          triggerFallbackSearch(controller.signal)
        } else {
          console.log('[Flights] Orchestrator already ran all fallbacks - skipping client-side fallback')
        }
      }

    } catch (err: any) {
      // Don't show error if request was aborted (user changed search)
      if (err.name === 'AbortError') {
        console.log('[Flights] Request aborted')
        return
      }

      console.error('Search error:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch results')
    } finally {
      setLoading(false)
      setLoadingTimeout(false)
      setShowRetry(false)
    }
  }
  
  // Trigger fallback search when primary returns 0 results
  const triggerFallbackSearch = async (abortSignal: AbortSignal) => {
    try {
      setLoadingFallback(true)
      setFallbackSuggestions(null)
      
      // Build search params
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
      
      // Run fallback searches (max 4 API calls)
      const suggestions = await runFallbackSearches(params, abortSignal)
      
      setFallbackSuggestions(suggestions)
    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.log('[Fallback] Request aborted')
        return
      }
      console.error('[Fallback] Error:', err)
    } finally {
      setLoadingFallback(false)
    }
  }

  // Helper function to process flight data
  const processFlightData = (fetchedOffers: FlightOffer[]) => {
    // Cache minimum price for this date
    if (fetchedOffers.length > 0) {
      const minPrice = Math.min(...fetchedOffers.map((o: FlightOffer) => o.price))
      setDatePriceCache((prev) => {
        const newCache = new Map(prev)
        newCache.set(selectedDate, minPrice)
        return newCache
      })

      // Initialize filters based on available data
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
  }

  // Manual retry function
  const handleRetry = () => {
    setError(null)
    setLoadingTimeout(false)
    setShowRetry(false)
    fetchResults()
  }

  // Calculate tab prices and durations (Best/Cheapest/Fastest)
  const { tabPrices, tabDurations } = useMemo(() => {
    if (filteredOffers.length === 0) {
      return { 
        tabPrices: { best: undefined, cheapest: undefined, fastest: undefined },
        tabDurations: { best: undefined, cheapest: undefined, fastest: undefined }
      }
    }

    // Cheapest: flight with minimum price
    const cheapestFlight = filteredOffers.reduce((min, offer) => 
      offer.price < min.price ? offer : min
    , filteredOffers[0]) // Provide initial value

    // Fastest: flight with minimum duration
    const fastestFlight = filteredOffers.reduce((min, offer) => 
      (offer.total_duration_minutes || 0) < (min.total_duration_minutes || 0) ? offer : min
    , filteredOffers[0]) // Provide initial value

    // Best: first flight when sorted by "best" logic (balanced price + duration)
    const bestSorted = [...filteredOffers].sort((a, b) => {
      const scoreA = a.price / 1000 + (a.total_duration_minutes || 0) / 60
      const scoreB = b.price / 1000 + (b.total_duration_minutes || 0) / 60
      return scoreA - scoreB
    })
    const bestFlight = bestSorted[0]

    return {
      tabPrices: {
        best: bestFlight?.price,
        cheapest: cheapestFlight?.price,
        fastest: fastestFlight?.price
      },
      tabDurations: {
        best: bestFlight?.total_duration_minutes || undefined,
        cheapest: cheapestFlight?.total_duration_minutes || undefined,
        fastest: fastestFlight?.total_duration_minutes || undefined
      }
    }
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
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <FlightLoadingState origin={origin} destination={destination} />
        
        {/* Loading timeout message */}
        {loadingTimeout && (
          <div className="max-w-2xl mx-auto mt-8 px-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
              <div className="flex items-center justify-center mb-3">
                <Loader2 className="h-5 w-5 animate-spin text-blue-600 mr-2" />
                <p className="text-blue-900 font-medium">
                  This is taking longer than usual
                </p>
              </div>
              <p className="text-sm text-blue-700">
                Prices will be confirmed on the partner site. We're still searching...
              </p>
            </div>
          </div>
        )}

        {/* Retry option after 12 seconds */}
        {showRetry && (
          <div className="max-w-2xl mx-auto mt-4 px-4">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
              <p className="text-yellow-900 mb-4">
                The search is taking unusually long. This may be due to slow provider responses.
              </p>
              <div className="flex justify-center gap-4">
                <button
                  onClick={handleRetry}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Retry Search
                </button>
                <button
                  onClick={() => router.push('/')}
                  className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  Go Back
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // Handle service unavailable
  if (serviceUnavailable) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <ServiceUnavailable 
          service="Flights"
          onRetry={() => {
            setServiceUnavailable(false)
            fetchResults()
          }}
        />
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
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        
        <NoFlightsWithSuggestions
          origin={origin}
          destination={destination}
          date={selectedDate}
          tripType={tripType}
          suggestions={fallbackSuggestions}
          isLoadingSuggestions={loadingFallback}
          onTryAgain={() => router.push('/')}
        />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      {/* TrustStrip removed - TrustIndicators in results section provides trust signals */}

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
      
      {/* Fallback Results Banner */}
      {showingFallbackResults && (
        <div className="bg-blue-50 border-b border-blue-200">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <div className="flex items-center gap-2 text-sm">
              <svg className="w-5 h-5 text-blue-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-blue-900">
                <strong>Showing flights from nearby airports.</strong> No direct flights were available from <strong>{origin}</strong> to <strong>{destination}</strong> on this date. Results include flights from regional hubs and nearby departure airports.
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Sort Tabs */}
      <SortTabs
        activeSort={sortType}
        onSortChange={setSortType}
        prices={tabPrices}
        durations={tabDurations}
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
            {/* Phase 2: Results Header - Decision Confidence Zone */}
            <div className="mb-6">
              {/* Row 1: SaveSearchButton (left) + TrackPrice (right) */}
              <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
                <SaveSearchButton
                  searchParams={{
                    origin,
                    destination,
                    departureDate: selectedDate,
                    returnDate: returnDate || undefined,
                    adults: parseInt(adults || '1'),
                    cabinClass: cabinClass || 'economy',
                    tripType: tripType || 'oneway',
                  }}
                  lastKnownPrice={offers.length > 0 ? Math.min(...offers.map(o => o.price || Infinity)) : undefined}
                  lastKnownCurrency={offers[0]?.currency || 'INR'}
                />
                <TrackPrice
                  origin={origin}
                  destination={destination}
                  departureDate={selectedDate}
                  returnDate={returnDate || undefined}
                />
              </div>
              
              {/* Row 2: TrustIndicators */}
              <TrustIndicators />
              
              {/* Row 3: PriceComparisonNotice */}
              <PriceComparisonNotice />
            </div>

            {/* Results count with price source indicator */}
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
              <p className="text-gray-600 text-sm">
                {filteredOffers.length === offers.length
                  ? `${offers.length} flight${offers.length !== 1 ? 's' : ''} found`
                  : `${filteredOffers.length} of ${offers.length} flights`}
              </p>
              
              {/* Price Source Badge - Shows "Live price" or "Showing recent prices" */}
              {searchSource && (
                <PriceSourceBadge
                  isLive={isLiveResults}
                  timestampDisplay={lastUpdatedAt}
                  helperText={cacheMessage ? "Prices may change on the booking site" : undefined}
                />
              )}}
            </div>

            {/* Flight Cards */}
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

            {/* Phase 2: Below Results - Platform Explanation */}
            <PlatformExplanation />
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
