'use client'

import { useState } from 'react'
import {
  Bus,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Clock,
  MapPin,
  Wifi,
  BatteryCharging,
  Snowflake,
  Info,
} from 'lucide-react'
import PriceDisplay from '@/components/ui/PriceDisplay'

interface BusOffer {
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
  operator_name: string
  operator_type: string
  bus_type: string
  bus_type_label: string
  is_ac: boolean
  is_sleeper: boolean
  has_charging_point: boolean
  has_wifi: boolean
  frequency: string | null
  departure_window: string | null
  stops_count: number
  intermediate_stops: string[]
}

interface BusCardProps {
  offer: BusOffer
}

export default function BusCard({ offer }: BusCardProps) {
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

  const handleBookingClick = (partner: BusOffer['booking_partners'][0]) => {
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
        {/* Bus Info Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
              <Bus className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="font-semibold text-gray-900">{offer.operator_name}</p>
              <p className="text-sm text-gray-500">{offer.bus_type_label}</p>
            </div>
          </div>
          
          {/* Amenities badges */}
          {!offer.is_fallback && (
            <div className="flex gap-2">
              {offer.is_ac && (
                <span className="flex items-center gap-1 px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded">
                  <Snowflake className="h-3 w-3" /> AC
                </span>
              )}
              {offer.is_sleeper && (
                <span className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded">
                  Sleeper
                </span>
              )}
            </div>
          )}
        </div>

        {/* Route & Time */}
        {!offer.is_fallback && (
          <div className="flex items-center justify-between mb-4">
            <div className="flex-1">
              <p className="text-2xl font-bold text-gray-900">{formatTime(offer.departure_time)}</p>
              <p className="text-sm text-gray-600">{offer.from_city}</p>
              <p className="text-xs text-gray-400 truncate">{offer.from_station_name}</p>
            </div>
            
            <div className="flex-1 flex flex-col items-center px-4">
              <p className="text-sm text-gray-500">{formatDuration(offer.duration_minutes)}</p>
              <div className="w-full h-0.5 bg-gray-200 my-1 relative">
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-orange-500 rounded-full" />
                <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-orange-500 rounded-full" />
              </div>
              {offer.distance_km && (
                <p className="text-xs text-gray-400">{offer.distance_km} km</p>
              )}
            </div>
            
            <div className="flex-1 text-right">
              <p className="text-2xl font-bold text-gray-900">{formatTime(offer.arrival_time)}</p>
              <p className="text-sm text-gray-600">{offer.to_city}</p>
              <p className="text-xs text-gray-400 truncate">{offer.to_station_name}</p>
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

        {/* Price */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-baseline gap-2">
              <PriceDisplay price={offer.avg_price} currency={offer.currency} className="text-2xl font-bold text-green-600" showTrustLabel={false} />
              <span className="text-sm text-gray-500">/ seat</span>
            </div>
            <p className="text-xs text-gray-400">{offer.price_label}</p>
          </div>
          
          {/* Additional amenities */}
          {!offer.is_fallback && (
            <div className="flex gap-2">
              {offer.has_wifi && (
                <div className="flex items-center gap-1 text-gray-500" title="WiFi Available">
                  <Wifi className="h-4 w-4" />
                </div>
              )}
              {offer.has_charging_point && (
                <div className="flex items-center gap-1 text-gray-500" title="Charging Available">
                  <BatteryCharging className="h-4 w-4" />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Expand Details Button */}
        {!offer.is_fallback && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1 text-sm text-orange-600 hover:text-orange-800 mb-4"
          >
            {showDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            {showDetails ? 'Hide details' : 'Show details'}
          </button>
        )}

        {/* Expanded Details */}
        {showDetails && !offer.is_fallback && (
          <div className="border-t pt-4 mb-4 space-y-3">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span>Operator Type: {offer.operator_type === 'government' ? 'Government RTC' : 'Private'}</span>
            </div>
            {offer.frequency && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Clock className="h-4 w-4" />
                <span>Frequency: {offer.frequency}</span>
              </div>
            )}
            {offer.departure_window && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span>Departures: {offer.departure_window}</span>
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
                className="flex items-center gap-1 px-3 py-2 text-sm bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition disabled:opacity-50"
              >
                {redirecting === partner.name ? (
                  'Redirecting...'
                ) : (
                  <>
                    {partner.name}
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
