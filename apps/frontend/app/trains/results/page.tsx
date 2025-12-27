'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Navigation from '@/components/layout/Navigation'
import TrainCard from '@/components/results/TrainCard'
import { Loader2, Train, ArrowLeft, AlertCircle } from 'lucide-react'
import { apiFetch } from '@/lib/api'

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

function TrainResultsContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  
  const origin = searchParams.get('origin') || ''
  const destination = searchParams.get('destination') || ''
  const departureDate = searchParams.get('departure_date') || ''
  const trainClass = searchParams.get('train_class') || ''
  const passengers = searchParams.get('passengers') || '1'
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<TrainSearchResponse | null>(null)
  const [sortBy, setSortBy] = useState<'departure' | 'duration' | 'price'>('departure')
  
  useEffect(() => {
    const fetchTrains = async () => {
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
        
        if (trainClass) {
          params.append('train_class', trainClass)
        }
        
        const response = await apiFetch(`/api/search/trains?${params}`)
        
        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.detail || 'Failed to search trains')
        }
        
        const data: TrainSearchResponse = await response.json()
        setResults(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred')
      } finally {
        setLoading(false)
      }
    }
    
    fetchTrains()
  }, [origin, destination, departureDate, trainClass, passengers])
  
  // Sort offers
  const sortedOffers = results?.offers ? [...results.offers].sort((a, b) => {
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
  }) : []
  
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    })
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => router.push('/')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to search
          </button>
          
          <div className="flex items-center gap-3 mb-2">
            <Train className="h-6 w-6 text-blue-600" />
            <h1 className="text-2xl font-bold text-gray-900">
              Trains from {results?.origin_city || origin} to {results?.destination_city || destination}
            </h1>
          </div>
          <p className="text-gray-600">
            {formatDate(departureDate)} • {passengers} passenger{parseInt(passengers) > 1 ? 's' : ''}
            {trainClass && ` • ${trainClass} class`}
          </p>
        </div>
        
        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
            <p className="text-gray-600">Searching for trains...</p>
          </div>
        )}
        
        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <AlertCircle className="h-8 w-8 text-red-600 mx-auto mb-4" />
            <p className="text-red-800 font-medium mb-2">Search Error</p>
            <p className="text-red-600">{error}</p>
            <button
              onClick={() => router.push('/')}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Try Again
            </button>
          </div>
        )}
        
        {/* Results */}
        {!loading && !error && results && (
          <>
            {/* Fallback Notice */}
            {results.is_fallback && results.fallback_message && (
              <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-amber-800">{results.fallback_message}</p>
              </div>
            )}
            
            {/* Sort Controls */}
            {!results.is_fallback && sortedOffers.length > 1 && (
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
                      {option.charAt(0).toUpperCase() + option.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            {/* Results Count */}
            <p className="text-sm text-gray-600 mb-4">
              {sortedOffers.length} train{sortedOffers.length !== 1 ? 's' : ''} found
              {results.distance_km && ` • ${results.distance_km} km`}
            </p>
            
            {/* Train Cards */}
            <div className="space-y-4">
              {sortedOffers.map(offer => (
                <TrainCard key={offer.offer_id} offer={offer} />
              ))}
            </div>
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
