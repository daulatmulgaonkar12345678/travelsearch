'use client'

import { useEffect, useState, Suspense, useRef } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import TrustStrip from '@/components/layout/TrustStrip'
import HotelLoadingState from '@/components/loading/HotelLoadingState'
import { Loader2, MapPin, Star, Hotel as HotelIcon, RefreshCw } from 'lucide-react'
import { API_ENDPOINTS, apiFetch } from '@/lib/config'
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

  // Get search parameters
  const city = searchParams.get('city') || ''
  const checkIn = searchParams.get('check_in') || ''
  const checkOut = searchParams.get('check_out') || ''
  const roomsCount = parseInt(searchParams.get('rooms') || '1', 10)
  
  // Extract rooms configuration from search params (safe to use in dependency array)
  const rooms = getRoomsFromSearchParams(searchParams)
  const roomsKey = JSON.stringify(rooms) // Stable key for dependency tracking

  useEffect(() => {
    if (!city || !checkIn || !checkOut) {
      setError('Missing required search parameters')
      setLoading(false)
      return
    }

    const fetchResults = async () => {
      try {
        setLoading(true)
        setError(null)

        const requestBody = {
          city,
          check_in: checkIn,
          check_out: checkOut,
          rooms
        }

        const url = API_ENDPOINTS.searchHotels
        const response = await apiFetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody)
        })

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        setOffers(data.offers || [])
      } catch (err) {
        console.error('Hotel search error:', err)
        setError(err instanceof Error ? err.message : 'Failed to fetch hotels')
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
  }, [city, checkIn, checkOut, roomsKey])

  const handleSelectHotel = (offer: HotelOffer) => {
    // Navigate to vendor selection page
    const params = new URLSearchParams({
      offer_id: offer.offer_id,
      hotel_name: offer.hotel_name,
      city: offer.city,
      price: offer.total_price.toString(),
      currency: offer.currency,
      check_in: checkIn,
      check_out: checkOut,
    })
    router.push(`/hotels/vendors?${params.toString()}`)
  }

  if (loading) {
    return (
      <HotelLoadingState city={city} />
    )
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-red-900 mb-2">Search Error</h3>
          <p className="text-red-700">{error}</p>
          <button
            onClick={() => router.push('/hotels')}
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
        <HotelIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 mb-2">No hotels found</h3>
        <p className="text-gray-600 mb-4">
          We couldn't find any hotels in {city} for your dates.
        </p>
        <button
          onClick={() => router.push('/hotels')}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Try Another Search
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Search Summary */}
      <div className="mb-6 bg-white rounded-lg shadow-sm p-4 border border-gray-200">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-1">
              Hotels in {city}
            </h2>
            <p className="text-gray-600 text-sm">
              {checkIn} to {checkOut} • {roomsCount} room(s) • {offers.length} hotels found
            </p>
          </div>
          <button
            onClick={() => router.push('/hotels')}
            className="px-4 py-2 text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
          >
            Modify Search
          </button>
        </div>
      </div>

      {/* Hotel Results */}
      <div className="space-y-4">
        {offers.map((offer) => (
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
  )
}

export default function HotelResultsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <TrustStrip />
      <main className="container mx-auto px-4 py-8">
        <Suspense fallback={
          <div className="flex items-center justify-center min-h-[400px]">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
          </div>
        }>
          <HotelResultsContent />
        </Suspense>
      </main>
    </div>
  )
}
