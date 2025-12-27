'use client'

import { useState } from 'react'
import {
  Train,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Clock,
  MapPin,
  Utensils,
  Info,
} from 'lucide-react'
import PriceDisplay from '@/components/ui/PriceDisplay'

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

interface TrainCardProps {
  offer: TrainOffer
}

export default function TrainCard({ offer }: TrainCardProps) {
  const [showDetails, setShowDetails] = useState(false)
  const [redirecting, setRedirecting] = useState<string | null>(null)

  const formatTime = (iso: string) => {
    if (!iso || iso === '0001-01-01T00:00:00') return '--:--'
    return new Date(iso).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })
  }

  const formatDuration = (minutes: number) => {
    if (!minutes) return 'Duration varies'
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}h ${mins}m`
  }

  const handleBookingClick = (partner: TrainOffer['booking_partners'][0]) => {
    setRedirecting(partner.name)
    setTimeout(() => {
      window.open(partner.url, '_blank')
      setRedirecting(null)
    }, 500)
  }

  // Sort booking partners by priority
  const sortedPartners = [...offer.booking_partners].sort((a, b) => a.priority - b.priority)

  return (
    <div className="relative bg-white border rounded-lg shadow-sm hover:shadow-md transition">
      {/* Fallback Badge */}
      {offer.is_fallback && (
        <div className="absolute top-3 right-3">
          <span className="px-2 py-1 text-xs font-medium bg-amber-100 text-amber-700 rounded-full">
            Redirect Only
          </span>
        </div>
      )}

      <div className="p-4">
        {/* Train Info Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <Train className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <p className="font-semibold text-gray-900">
              {offer.train_name}
              {!offer.is_fallback && (
                <span className="ml-2 text-sm font-normal text-gray-500">#{offer.train_number}</span>
              )}
            </p>
            {offer.train_type && (
              <p className="text-sm text-gray-500">{offer.train_type}</p>
            )}
          </div>
        </div>

        {/* Route & Time */}
        {!offer.is_fallback && (
          <div className="flex items-center justify-between mb-4">
            <div className="flex-1">
              <p className="text-2xl font-bold text-gray-900">{formatTime(offer.departure_time)}</p>
              <p className="text-sm text-gray-600">{offer.from_station}</p>
              <p className="text-xs text-gray-400">{offer.from_city}</p>
            </div>
            
            <div className="flex-1 flex flex-col items-center px-4">
              <p className="text-sm text-gray-500">{formatDuration(offer.duration_minutes)}</p>
              <div className="w-full h-0.5 bg-gray-200 my-1 relative">
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-blue-500 rounded-full" />
                <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-blue-500 rounded-full" />
              </div>
              <p className="text-xs text-gray-400">
                {offer.stops_count === 0 ? 'Direct' : `${offer.stops_count} stop${offer.stops_count > 1 ? 's' : ''}`}
              </p>
            </div>
            
            <div className="flex-1 text-right">
              <p className="text-2xl font-bold text-gray-900">{formatTime(offer.arrival_time)}</p>
              <p className="text-sm text-gray-600">{offer.to_station}</p>
              <p className="text-xs text-gray-400">{offer.to_city}</p>
            </div>
          </div>
        )}

        {/* Fallback Message */}
        {offer.is_fallback && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex gap-2">
              <Info className="h-5 w-5 text-amber-600 flex-shrink-0" />
              <p className="text-sm text-amber-800">
                This route is not in our database. Check our booking partners for live schedules and availability.
              </p>
            </div>
          </div>
        )}

        {/* Price & Classes */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-baseline gap-2">
              <PriceDisplay price={offer.avg_price} currency={offer.currency} className="text-2xl font-bold text-green-600" showTrustLabel={false} />
              <span className="text-sm text-gray-500">/ person</span>
            </div>
            <p className="text-xs text-gray-400">{offer.price_label}</p>
          </div>
          
          {!offer.is_fallback && offer.has_pantry && (
            <div className="flex items-center gap-1 text-gray-500">
              <Utensils className="h-4 w-4" />
              <span className="text-xs">Pantry</span>
            </div>
          )}
        </div>

        {/* Available Classes */}
        {!offer.is_fallback && offer.available_classes.length > 0 && (
          <div className="mb-4">
            <p className="text-xs text-gray-500 mb-2">Available Classes:</p>
            <div className="flex flex-wrap gap-2">
              {offer.available_classes.map(cls => (
                <span
                  key={cls.class}
                  className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
                >
                  {cls.class}: ₹{cls.avg_fare.toLocaleString()}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Expand Details Button */}
        {!offer.is_fallback && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 mb-4"
          >
            {showDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            {showDetails ? 'Hide details' : 'Show details'}
          </button>
        )}

        {/* Expanded Details */}
        {showDetails && !offer.is_fallback && (
          <div className="border-t pt-4 mb-4 space-y-3">
            {offer.frequency && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Clock className="h-4 w-4" />
                <span>Runs: {offer.frequency}</span>
              </div>
            )}
            {offer.days_of_operation.length > 0 && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span>Days: {offer.days_of_operation.join(', ')}</span>
              </div>
            )}
            {offer.distance_km && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <MapPin className="h-4 w-4" />
                <span>Distance: {offer.distance_km} km</span>
              </div>
            )}
          </div>
        )}

        {/* Booking Partners */}
        <div className="border-t pt-4">
          <p className="text-xs text-gray-500 mb-2">Book on:</p>
          <div className="flex flex-wrap gap-2">
            {sortedPartners.map(partner => (
              <button
                key={partner.name}
                onClick={() => handleBookingClick(partner)}
                disabled={redirecting === partner.name}
                className={`flex items-center gap-1 px-3 py-2 text-sm rounded-lg transition ${
                  partner.is_official
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                } disabled:opacity-50`}
              >
                {redirecting === partner.name ? (
                  'Redirecting...'
                ) : (
                  <>
                    {partner.name}
                    {partner.is_official && <span className="text-xs">(Official)</span>}
                    <ExternalLink className="h-3 w-3" />
                  </>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Disclaimer */}
        <p className="mt-3 text-xs text-gray-400">{offer.price_disclaimer}</p>
      </div>
    </div>
  )
}
