'use client'

import { Plane, Clock, Briefcase, Leaf } from 'lucide-react'
import { formatCurrency, formatDuration } from '@/lib/utils'
import ProviderOfferCard from './ProviderOfferCard'
import { useState } from 'react'

export type Segment = {
  departure_airport: string
  arrival_airport: string
  departure_time: string
  arrival_time: string
  carrier_code: string
  carrier_name: string
  flight_number?: string
  duration_minutes?: number
  aircraft_type?: string
}

export type ProviderOffer = {
  name: string
  price: number
  deep_link: string
  rating?: number
  promo?: string
  trust_bullets?: string[]
}

export type FlightOffer = {
  offer_id: string
  provider: string
  price: number
  currency: string
  segments: Segment[]
  total_duration_minutes: number
  stops: number
  baggage_allowance?: string
  cabin_class?: string
  fare_rules?: string
  emissions_kg?: number
  deep_link?: string
  rating?: number
  providers?: ProviderOffer[]
}

interface ResultCardProps {
  offer: FlightOffer
  onProviderSelect?: (provider: ProviderOffer, offer: FlightOffer) => void
  badge?: 'best' | 'cheapest' | 'fastest'
}

export default function ResultCard({ offer, onProviderSelect, badge }: ResultCardProps) {
  const [showAllProviders, setShowAllProviders] = useState(false)
  
  const firstSegment = offer.segments[0]
  const lastSegment = offer.segments[offer.segments.length - 1]
  
  const formatTime = (isoDate: string) => {
    const date = new Date(isoDate)
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
  }

  const formatDate = (isoDate: string) => {
    const date = new Date(isoDate)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  const layoverInfo = offer.segments.length > 1 ? (
    offer.segments.slice(0, -1).map((seg, idx) => {
      const nextSeg = offer.segments[idx + 1]
      const layoverMinutes = (new Date(nextSeg.departure_time).getTime() - new Date(seg.arrival_time).getTime()) / 60000
      return {
        airport: seg.arrival_airport,
        duration: Math.round(layoverMinutes)
      }
    })
  ) : []

  const badgeConfig = {
    best: { text: 'Best Value', className: 'bg-blue-100 text-blue-700' },
    cheapest: { text: 'Cheapest', className: 'bg-green-100 text-green-700' },
    fastest: { text: 'Fastest', className: 'bg-purple-100 text-purple-700' },
  }

  const displayedProviders = showAllProviders ? (offer.providers || []) : (offer.providers || []).slice(0, 1)

  return (
    <article
      data-testid={`result-card-${offer.offer_id}`}
      className="bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-lg transition-all overflow-hidden"
      aria-labelledby={`offer-${offer.offer_id}`}
    >
      {/* Badge */}
      {badge && (
        <div className={`px-4 py-2 text-xs font-semibold ${badgeConfig[badge].className}`}>
          {badgeConfig[badge].text}
        </div>
      )}

      <div className="p-6">
        <div className="grid md:grid-cols-[1fr,auto] gap-6">
          {/* Flight Details */}
          <div className="space-y-4">
            {/* Airline Info */}
            <div className="flex items-center space-x-3">
              <div className="h-12 w-12 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <Plane className="h-6 w-6 text-gray-600" />
              </div>
              <div>
                <h3 id={`offer-${offer.offer_id}`} className="text-lg font-semibold text-gray-900">
                  {firstSegment.carrier_name}
                </h3>
                <p className="text-sm text-gray-500">
                  {firstSegment.flight_number} • {firstSegment.aircraft_type || 'Aircraft'}
                </p>
              </div>
            </div>

            {/* Route & Time */}
            <div className="flex items-center space-x-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {formatTime(firstSegment.departure_time)}
                </div>
                <div className="text-sm text-gray-600">
                  {firstSegment.departure_airport}
                </div>
                <div className="text-xs text-gray-500">
                  {formatDate(firstSegment.departure_time)}
                </div>
              </div>

              <div className="flex-1 relative">
                <div className="border-t-2 border-gray-300 relative">
                  {offer.stops > 0 && (
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white px-2">
                      <div className="h-2 w-2 rounded-full bg-gray-400"></div>
                    </div>
                  )}
                </div>
                <div className="flex items-center justify-center space-x-2 mt-2">
                  <Clock className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-600">
                    {formatDuration(offer.total_duration_minutes)}
                  </span>
                </div>
                <div className="text-xs text-center text-gray-500 mt-1">
                  {offer.stops === 0 ? 'Non-stop' : `${offer.stops} stop${offer.stops > 1 ? 's' : ''}`}
                </div>
              </div>

              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {formatTime(lastSegment.arrival_time)}
                </div>
                <div className="text-sm text-gray-600">
                  {lastSegment.arrival_airport}
                </div>
                <div className="text-xs text-gray-500">
                  {formatDate(lastSegment.arrival_time)}
                </div>
              </div>
            </div>

            {/* Layover Info */}
            {layoverInfo.length > 0 && (
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-xs font-medium text-gray-700 mb-1">Layovers:</div>
                {layoverInfo.map((layover, idx) => (
                  <div key={idx} className="text-xs text-gray-600">
                    {layover.airport}: {formatDuration(layover.duration)}
                  </div>
                ))}
              </div>
            )}

            {/* Additional Info */}
            <div className="flex flex-wrap gap-4 text-sm text-gray-600">
              {offer.baggage_allowance && (
                <div className="flex items-center space-x-2">
                  <Briefcase className="h-4 w-4" />
                  <span>{offer.baggage_allowance}</span>
                </div>
              )}
              {offer.emissions_kg && (
                <div className="flex items-center space-x-2">
                  <Leaf className="h-4 w-4 text-green-600" />
                  <span>{offer.emissions_kg}kg CO₂</span>
                </div>
              )}
            </div>
          </div>

          {/* Price & Providers */}
          <div className="md:min-w-[300px] space-y-4">
            <div className="text-right md:text-left">
              <div className="text-sm text-gray-500">From</div>
              <div className="text-3xl font-bold text-gray-900">
                {formatCurrency(offer.price, offer.currency)}
              </div>
              {offer.rating && (
                <div className="text-sm text-gray-600 mt-1">
                  Rating: {offer.rating}/100
                </div>
              )}
            </div>

            {/* Provider Offers */}
            <div className="space-y-2">
              {displayedProviders.map((provider) => (
                <ProviderOfferCard
                  key={provider.name}
                  provider={provider}
                  currency={offer.currency}
                  onSelect={() => onProviderSelect?.(provider, offer)}
                />
              ))}

              {(offer.providers?.length || 0) > 1 && !showAllProviders && (
                <button
                  data-testid="show-all-providers"
                  onClick={() => setShowAllProviders(true)}
                  className="w-full py-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  + {(offer.providers?.length || 0) - 1} more provider{(offer.providers?.length || 0) - 1 > 1 ? 's' : ''}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </article>
  )
}
