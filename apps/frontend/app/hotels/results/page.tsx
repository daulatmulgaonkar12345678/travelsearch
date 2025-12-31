'use client'

import { useEffect, useState, Suspense, useRef, useMemo } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import HotelLoadingState from '@/components/loading/HotelLoadingState'
import ServiceUnavailable from '@/components/common/ServiceUnavailable'
import NoResultsState from '@/components/common/NoResultsState'
import ServiceError, { getErrorType, ErrorType } from '@/components/common/ServiceError'
import { Loader2, MapPin, Star, Hotel as HotelIcon, RefreshCw, Search, X } from 'lucide-react'
import { apiFetch } from '@/lib/api'
import ModifySearchButton from '@/components/search/ModifySearchButton'
import { requestCache } from '@/lib/requestCache'

interface HotelOffer {
  offer_id: string
  provider: string
  hotel_name: string
  address: string
  city: string
  rating?: number
  review_score?: number
  price_per_night: number
  total_price: number
  currency: string
  amenities: string[]
  room_type: string
  cancellation_policy: string
  deep_link: string
}

type RoomConfig = {
  adults: number
  children: number[]
}

function getRoomsFromSearchParams(searchParams: URLSearchParams): RoomConfig[] {
  const roomCount = Number(searchParams.get('rooms') ?? '1')
  const rooms: RoomConfig[] = []

  for (let i = 0; i < roomCount; i++) {
    const adults = Number(searchParams.get(`room_${i}_adults`) ?? '2')
    const children: number[] = []
    let childIndex = 0
    while (searchParams.has(`room_${i}_child_${childIndex}_age`)) {
      children.push(Number(searchParams.get(`room_${i}_child_${childIndex}_age`) ?? '0'))
      childIndex++
    }
    rooms.push({ adults, children })
  }

  return rooms.length > 0 ? rooms : [{ adults: 2, children: [] }]
}

function HotelResultsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [offers, setOffers] = useState<HotelOffer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [serviceUnavailable, setServiceUnavailable] = useState(false)
  const [loadingTimeout, setLoadingTimeout] = useState(false)
  const [showRetry, setShowRetry] = useState(false)
  
  // Local hotel name filter (post-search filtering)
  const [hotelNameFilter, setHotelNameFilter] = useState('')

  // Abort controller ref for cancelling requests
  const abortControllerRef = useRef<AbortController | null>(null)

  // Get search parameters
  const city = searchParams.get('city') || ''
  const checkIn = searchParams.get('check_in') || ''
  const checkOut = searchParams.get('check_out') || ''
  const roomsCount = parseInt(searchParams.get('rooms') || '1', 10)
  
  // Search intent parameters (CITY/AREA/HOTEL)
  const searchType = searchParams.get('search_type') || 'CITY'
  const area = searchParams.get('area') || ''
  const lat = searchParams.get('lat') || ''
  const lng = searchParams.get('lng') || ''
  const hotelId = searchParams.get('hotel_id') || ''
  const hotelName = searchParams.get('hotel_name') || ''
  
  // Extract rooms configuration from search params (safe to use in dependency array)
  const rooms = getRoomsFromSearchParams(searchParams)
  const roomsKey = JSON.stringify(rooms) // Stable key for dependency tracking
  
  // Create stable search intent key for dependency tracking
  const searchIntentKey = `${searchType}:${area}:${hotelId}`

  useEffect(() => {
    if (!city || !checkIn || !checkOut) {
      setError('Missing required search parameters')
      setLoading(false)
      return
    }

    // Abort previous request if search params changed
    if (abortControllerRef.current) {
      console.log('[Hotels] Aborting previous search')
      abortControllerRef.current.abort()
    }

    fetchResults()

    // Cleanup on unmount
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [city, checkIn, checkOut, roomsKey, searchIntentKey])

  const fetchResults = async () => {
    try {
      setLoading(true)
      setError(null)
      setLoadingTimeout(false)
      setShowRetry(false)

      // Build request body with search intent (CITY/AREA/HOTEL)
      const requestBody: Record<string, any> = {
        city,
        check_in: checkIn,
        check_out: checkOut,
        rooms,
        search_type: searchType,
      }
      
      // Add AREA-specific parameters
      if (searchType === 'AREA') {
        if (area) requestBody.area = area
        if (lat) requestBody.latitude = parseFloat(lat)
        if (lng) requestBody.longitude = parseFloat(lng)
      }
      
      // Add HOTEL-specific parameters
      if (searchType === 'HOTEL') {
        if (hotelId) requestBody.hotel_id = hotelId
        if (hotelName) requestBody.hotel_name = hotelName
      }

      // Check cache first
      const cached = requestCache.get<any>('hotels', requestBody)
      if (cached) {
        console.log('[Hotels] Using cached data')
        setOffers(cached.offers || [])
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

      const response = await apiFetch('/api/search/hotels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
        signal: controller.signal
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

      // Cache the response
      requestCache.set('hotels', requestBody, data)

      setOffers(data.offers || [])
    } catch (err: any) {
      // Don't show error if request was aborted (user changed search)
      if (err.name === 'AbortError') {
        console.log('[Hotels] Request aborted')
        return
      }

      console.error('Hotel search error:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch hotels')
    } finally {
      setLoading(false)
      setLoadingTimeout(false)
      setShowRetry(false)
    }
  }

  // Manual retry function
  const handleRetry = () => {
    setError(null)
    setLoadingTimeout(false)
    setShowRetry(false)
    fetchResults()
  }

  const handleSelectHotel = (offer: HotelOffer) => {
    // Navigate to vendor selection page with search intent
    const params = new URLSearchParams({
      offer_id: offer.offer_id,
      hotel_name: offer.hotel_name,
      city: offer.city,
      price: offer.total_price.toString(),
      currency: offer.currency,
      check_in: checkIn,
      check_out: checkOut,
      // Include search intent for analytics
      search_type: searchType,
    })
    
    // Add AREA if applicable
    if (searchType === 'AREA' && area) {
      params.set('area', area)
    }
    
    router.push(`/hotels/vendors?${params.toString()}`)
  }

  // Generate contextual subtitle based on search type
  const getSearchContextSubtitle = () => {
    if (searchType === 'AREA' && area) {
      return `Showing hotels in ${area}, ${city}`
    }
    return `Hotels in ${city}`
  }
  
  // Local hotel name filter - filter results client-side
  // Must be called before any early returns to follow React hooks rules
  const filteredOffers = useMemo(() => {
    if (!hotelNameFilter.trim()) {
      return offers
    }
    const filterLower = hotelNameFilter.toLowerCase().trim()
    return offers.filter(offer => 
      offer.hotel_name.toLowerCase().includes(filterLower)
    )
  }, [offers, hotelNameFilter])

  // Handle service unavailable
  if (serviceUnavailable) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <ServiceUnavailable 
          service="Hotels"
          onRetry={() => {
            setServiceUnavailable(false)
            fetchResults()
          }}
        />
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <HotelLoadingState city={city} />
        
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
                  onClick={() => router.push('/hotels')}
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

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="max-w-2xl mx-auto py-12 px-4">
          <ServiceError 
            type={getErrorType(undefined, new Error(error))}
            onRetry={handleRetry}
            onGoBack={() => router.push('/hotels')}
            technicalDetails={error}
          />
        </div>
      </div>
    )
  }

  if (offers.length === 0) {
    // Custom message for AREA search or general no results
    const noResultsMessage = () => {
      if (searchType === 'AREA' && area) {
        return {
          title: `No hotels found in ${area}`,
          description: `We couldn't find any hotels in ${area}, ${city} for the selected dates. Try expanding your search to all of ${city}.`,
          icon: 'area'
        }
      }
      return {
        title: 'No hotels found',
        description: `We couldn't find any hotels in ${city} for the selected dates. Try different dates or another destination.`,
        icon: 'city'
      }
    }
    
    const msg = noResultsMessage()
    
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <div className="max-w-2xl mx-auto py-12 px-4">
          {/* Custom no results UI */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
            <div className={`w-16 h-16 rounded-full mx-auto mb-6 flex items-center justify-center ${
              msg.icon === 'area' ? 'bg-green-100' : 'bg-gray-100'
            }`}>
              {msg.icon === 'area' ? (
                <MapPin className="h-8 w-8 text-green-600" />
              ) : (
                <HotelIcon className="h-8 w-8 text-gray-600" />
              )}
            </div>
            
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {msg.title}
            </h2>
            <p className="text-gray-600 mb-6">
              {msg.description}
            </p>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <p className="text-blue-800 text-sm">
                💡 Some hotels may not be available for booking through our partners
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={() => router.push(`/?tab=hotels&city=${encodeURIComponent(city)}`)}
                className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition font-medium"
              >
                Search All Hotels in {city}
              </button>
              <button
                onClick={() => router.push('/?tab=hotels')}
                className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition font-medium"
              >
                New Search
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Main results view
  // Generate contextual subtitle based on search type
  const getSearchContextSubtitle = () => {
    if (searchType === 'AREA' && area) {
      return `Showing hotels in ${area}, ${city}`
    }
    return `Hotels in ${city}`
  }
  
  // Local hotel name filter - filter results client-side
  const filteredOffers = useMemo(() => {
    if (!hotelNameFilter.trim()) {
      return offers
    }
    const filterLower = hotelNameFilter.toLowerCase().trim()
    return offers.filter(offer => 
      offer.hotel_name.toLowerCase().includes(filterLower)
    )
  }, [offers, hotelNameFilter])
  
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Search Context Banner for AREA searches */}
        {searchType === 'AREA' && (
          <div className="mb-4 p-4 rounded-lg flex items-center gap-3 bg-green-50 border border-green-200">
            <MapPin className="h-5 w-5 text-green-600" />
            <div>
              <p className="font-medium text-green-800">Area Search</p>
              <p className="text-sm text-green-700">{getSearchContextSubtitle()}</p>
            </div>
          </div>
        )}
        
        {/* Search Summary with Modify Search */}
      <div className="mb-6 bg-white rounded-lg shadow-sm p-4 border border-gray-200">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-1">
              {getSearchContextSubtitle()}
            </h2>
            <p className="text-gray-600 text-sm">
              {checkIn} to {checkOut} • {roomsCount} room(s) • {filteredOffers.length} hotels{hotelNameFilter ? ' matching filter' : ' found'}
            </p>
          </div>
          <ModifySearchButton 
            service="hotels"
            searchParams={{
              city,
              check_in: checkIn,
              check_out: checkOut,
              adults: rooms[0]?.adults?.toString() || '2',
              // Include search intent for modify
              search_type: searchType,
              ...(searchType === 'AREA' && area && { area }),
            }}
            variant="default"
          />
        </div>
      </div>
      
      {/* Hotel Name Filter - Local filtering (Industry Standard) */}
      <div className="mb-4 bg-white rounded-lg shadow-sm p-4 border border-gray-200">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Filter by hotel name..."
              value={hotelNameFilter}
              onChange={(e) => setHotelNameFilter(e.target.value)}
              className="w-full pl-10 pr-10 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {hotelNameFilter && (
              <button
                onClick={() => setHotelNameFilter('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          💡 Some hotels may not be available for booking through our partners
        </p>
      </div>

      {/* No results after filtering */}
      {filteredOffers.length === 0 && hotelNameFilter && (
        <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200 text-center">
          <HotelIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No hotels match "{hotelNameFilter}"</h3>
          <p className="text-gray-600 mb-4">Try a different hotel name or clear the filter</p>
          <button
            onClick={() => setHotelNameFilter('')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Clear Filter
          </button>
        </div>
      )}

      {/* Hotel Results */}
      <div className="space-y-4">
        {filteredOffers.map((offer) => (
          <div
            key={offer.offer_id}
            className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
          >
            <div className="p-6">
              <div className="flex justify-between items-start gap-4">
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-1">
                        {offer.hotel_name}
                      </h3>
                      <div className="flex items-center text-gray-600 text-sm mb-2">
                        <MapPin className="h-4 w-4 mr-1" />
                        {offer.address}
                      </div>
                    </div>
                    {offer.rating && (
                      <div className="flex items-center bg-blue-600 text-white px-2 py-1 rounded">
                        <Star className="h-4 w-4 mr-1 fill-current" />
                        <span className="font-semibold">{offer.rating}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-2 mb-3">
                    <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                      {offer.room_type}
                    </span>
                    {offer.amenities.slice(0, 3).map((amenity, idx) => (
                      <span key={idx} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded">
                        {amenity}
                      </span>
                    ))}
                  </div>

                  <p className="text-sm text-gray-600">{offer.cancellation_policy}</p>
                </div>

                <div className="text-right">
                  <div className="mb-2">
                    <div className="text-2xl font-bold text-gray-900">
                      {offer.currency} {offer.total_price.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600">
                      {offer.currency} {offer.price_per_night.toLocaleString()} / night
                    </div>
                  </div>
                  <button
                    onClick={() => handleSelectHotel(offer)}
                    className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
                  >
                    View Vendors
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
    </div>
  )
}

/**
 * Hotel Results Page
 * 
 * Architecture aligned with Flights/Trains/Buses:
 * - Suspense wrapper only provides loading fallback
 * - Navigation is rendered ONCE inside HotelResultsContent
 * - No duplicate Header or TrustStrip
 */
export default function HotelResultsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
      </div>
    }>
      <HotelResultsContent />
    </Suspense>
  )
}
