'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import ResultCard, { FlightOffer } from '@/components/results/ResultCard'
import FilterSidebar from '@/components/results/FilterSidebar'
import DateStrip from '@/components/search/DateStrip'
import InterstitialRedirectModal from '@/components/common/InterstitialRedirectModal'
import { Loader2, SlidersHorizontal } from 'lucide-react'
import { API_ENDPOINTS, apiFetch } from '@/lib/config'

function SearchResultsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [offers, setOffers] = useState<FlightOffer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  
  // Redirect modal state
  const [redirectModal, setRedirectModal] = useState<{
    isOpen: boolean
    provider: string
    price: number
    currency: string
    redirectUrl: string
  }>({ isOpen: false, provider: '', price: 0, currency: 'INR', redirectUrl: '' })

  // Filter state
  const [filters, setFilters] = useState({
    stops: [] as string[],
    baggage: [] as string[],
    departureTime: [0, 23] as [number, number],
    arrivalTime: [0, 23] as [number, number],
    duration: [0, 24] as [number, number],
    airlines: [] as string[],
    emissions: false,
  })

  const [selectedDate, setSelectedDate] = useState<string>(searchParams.get('departure_date') || '')

  useEffect(() => {
    const fetchResults = async () => {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams({
        origin: searchParams.get('origin') || 'BOM',
        destination: searchParams.get('destination') || 'PNQ',
        departure_date: selectedDate || searchParams.get('departure_date') || '2025-12-15',
        adults: searchParams.get('adults') || '1',
        children: searchParams.get('children') || '0',
        infants: searchParams.get('infants') || '0',
      })

      try {
        const url = `${API_ENDPOINTS.searchFlights}?${params}`
        const response = await apiFetch(url)
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        
        // Transform backend offers to include mock providers
        const offersWithProviders = data.offers.map((offer: any) => ({
          ...offer,
          providers: [
            {
              name: offer.provider,
              price: offer.price,
              deep_link: offer.deep_link || 'https://mock-provider.com',
              rating: offer.rating || 85,
              trust_bullets: ['Secure payments', '24/7 support'],
            },
          ],
        }))
        
        setOffers(offersWithProviders)
      } catch (err) {
        console.error('Search error:', err)
        setError(err instanceof Error ? err.message : 'Failed to fetch results')
      } finally {
        setLoading(false)
      }
    }

    fetchResults()
  }, [searchParams, selectedDate])

  const handleProviderSelect = async (provider: any, offer: FlightOffer) => {
    // Navigate to vendor selection page with offer details
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
    
    const returnDate = searchParams.get('return_date')
    if (returnDate) {
      params.set('return_date', returnDate)
    }
    
    router.push(`/flights/vendors?${params.toString()}`)
    
    // Keep old modal logic as backup (commented out)
    /*
    try {
      const response = await apiFetch(API_ENDPOINTS.redirect, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: provider.name,
          offer_id: offer.offer_id,
          route: `${offer.segments[0].departure_airport}-${offer.segments[offer.segments.length - 1].arrival_airport}`,
          price: provider.price,
          deep_link: provider.deep_link,
        }),
      })

      const data = await response.json()

      // Show interstitial modal
      setRedirectModal({
        isOpen: true,
        provider: provider.name,
        price: provider.price,
        currency: offer.currency,
        redirectUrl: data.redirect_url,
      })
    } catch (err) {
      console.error('Redirect error:', err)
      // Fallback: direct redirect
      window.open(provider.deep_link, '_blank')
    }
  }

  const filterResults = (offers: FlightOffer[]) => {
    return offers.filter((offer) => {
      // Stops filter
      if (filters.stops.length > 0) {
        const stopMatch = filters.stops.some((stop) => {
          if (stop === 'Non-stop') return offer.stops === 0
          if (stop === '1 Stop') return offer.stops === 1
          if (stop === '2+ Stops') return offer.stops >= 2
          return false
        })
        if (!stopMatch) return false
      }

      // Duration filter (in hours)
      const durationHours = offer.total_duration_minutes / 60
      if (durationHours > filters.duration[1]) return false

      // Airlines filter
      if (filters.airlines.length > 0) {
        const airlineMatch = filters.airlines.some(
          (airline) => offer.segments[0].carrier_name === airline
        )
        if (!airlineMatch) return false
      }

      // Emissions filter
      if (filters.emissions && offer.emissions_kg && offer.emissions_kg > 80) {
        return false
      }

      return true
    })
  }

  const filteredOffers = filterResults(offers)

  // Determine badges
  const offersWithBadges = filteredOffers.map((offer, idx) => {
    if (idx === 0 && offer.rating && offer.rating >= 85) return { ...offer, badge: 'best' as const }
    if (offer.price === Math.min(...filteredOffers.map(o => o.price))) return { ...offer, badge: 'cheapest' as const }
    if (offer.total_duration_minutes === Math.min(...filteredOffers.map(o => o.total_duration_minutes))) {
      return { ...offer, badge: 'fastest' as const }
    }
    return offer
  })

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      {/* Date Strip */}
      <DateStrip selectedDate={selectedDate} onDateSelect={setSelectedDate} />

      <div className="container mx-auto px-4 py-8">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900">
            {searchParams.get('origin')} → {searchParams.get('destination')}
          </h1>
          <button
            data-testid="toggle-filters"
            onClick={() => setShowFilters(!showFilters)}
            className="md:hidden flex items-center space-x-2 px-4 py-2 bg-white border border-gray-200 rounded-lg"
          >
            <SlidersHorizontal className="h-5 w-5" />
            <span>Filters</span>
          </button>
        </div>

        <div className="flex flex-col md:flex-row gap-6">
          {/* Filters */}
          <aside className={`${showFilters ? 'block' : 'hidden'} md:block w-full md:w-80 flex-shrink-0`}>
            <FilterSidebar filters={filters} onFilterChange={setFilters} />
          </aside>

          {/* Results */}
          <main className="flex-1">
            {loading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                <span className="ml-3 text-gray-600">Searching flights...</span>
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                <p className="text-red-800">Error: {error}</p>
              </div>
            ) : filteredOffers.length === 0 ? (
              <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
                <p className="text-gray-600">No flights found matching your filters.</p>
                <button
                  onClick={() => setFilters({
                    stops: [],
                    baggage: [],
                    departureTime: [0, 23],
                    arrivalTime: [0, 23],
                    duration: [0, 24],
                    airlines: [],
                    emissions: false,
                  })}
                  className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
                >
                  Clear all filters
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="text-sm text-gray-600 mb-4">
                  {filteredOffers.length} flight{filteredOffers.length !== 1 ? 's' : ''} found
                </div>
                {offersWithBadges.map((offer) => (
                  <ResultCard
                    key={offer.offer_id}
                    offer={offer}
                    badge={'badge' in offer ? offer.badge : undefined}
                    onProviderSelect={handleProviderSelect}
                  />
                ))}
              </div>
            )}
          </main>
        </div>
      </div>

      {/* Interstitial Redirect Modal */}
      <InterstitialRedirectModal
        isOpen={redirectModal.isOpen}
        provider={redirectModal.provider}
        price={redirectModal.price}
        currency={redirectModal.currency}
        redirectUrl={redirectModal.redirectUrl}
        onClose={() => setRedirectModal({ ...redirectModal, isOpen: false })}
      />
    </div>
  )
}

export default function SearchResultsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    }>
      <SearchResultsContent />
    </Suspense>
  )
}
