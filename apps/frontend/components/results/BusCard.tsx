'use client'

import { useState, useCallback } from 'react'
import {
  Bus,
  ChevronDown,
  ChevronUp,
  Search,
  Clock,
  Wifi,
  BatteryCharging,
  Snowflake,
  MapPin,
  Route,
  Users,
} from 'lucide-react'
import LikelyStops from './LikelyStops'
import RedirectTransition from '@/components/loading/RedirectTransition'

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
  index?: number  // For stagger animation
}

// Button label mapping for each partner
const getPartnerButtonLabel = (partnerName: string): string => {
  const labels: Record<string, string> = {
    'redBus': '🔍 Search on redBus',
    'Paytm Bus': '🔍 Open Paytm Bus',
    'AbhiBus': '🔍 Open AbhiBus',
    'MSRTC Official': '🔍 Open MSRTC Official',
  }
  return labels[partnerName] || `🔍 Open ${partnerName}`
}

export default function BusCard({ offer, index = 0 }: BusCardProps) {
  const [showDetails, setShowDetails] = useState(false)
  const [redirecting, setRedirecting] = useState<string | null>(null)
  const [showFareTooltip, setShowFareTooltip] = useState(false)
  const [showRedirectTransition, setShowRedirectTransition] = useState(false)
  const [pendingRedirectUrl, setPendingRedirectUrl] = useState<string | null>(null)

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
  
  // Check if this is an estimated/state network result
  const isEstimatedResult = offer.provider === 'state_network' || offer.operator_name === 'Multiple Operators'
  
  // Calculate stagger class (max 8 levels)
  const staggerClass = `animate-stagger-${Math.min(index + 1, 8)}`

  return (
    <div className={`relative bg-white border rounded-lg shadow-sm hover:shadow-md transition-all duration-200 animate-card-in opacity-0 ${staggerClass}`}>
      <div className="p-4">
        {/* Bus Info Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
              <Bus className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <p className="font-semibold text-gray-900">
                  {/* 1️⃣ Operator Clarity: Add "Estimated Availability" for estimated results */}
                  {isEstimatedResult ? (
                    <>
                      <span className="flex items-center gap-1.5">
                        <Users className="h-4 w-4 text-gray-500" />
                        Multiple Operators
                        <span className="text-xs font-normal text-gray-500">(Estimated Availability)</span>
                      </span>
                    </>
                  ) : (
                    offer.operator_name
                  )}
                </p>
              </div>
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

        {/* Route & Time with Trust Indicators */}
        {!offer.is_fallback && (
          <div className="flex items-center justify-between mb-4">
            <div className="flex-1">
              <p className="text-2xl font-bold text-gray-900">{formatTime(offer.departure_time)}</p>
              <p className="text-sm text-gray-600">{offer.from_city}</p>
              <p className="text-xs text-gray-400 truncate">{offer.from_station_name}</p>
            </div>
            
            <div className="flex-1 flex flex-col items-center px-4">
              {/* 6️⃣ Visual Trust Indicators */}
              <div className="flex items-center gap-1 text-sm text-gray-500">
                <Clock className="h-3.5 w-3.5" />
                <span>{formatDuration(offer.duration_minutes)}</span>
              </div>
              <div className="w-full h-0.5 bg-gray-200 my-1 relative">
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-orange-500 rounded-full" />
                <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-2 bg-orange-500 rounded-full" />
              </div>
              {offer.distance_km && (
                <div className="flex items-center gap-1 text-xs text-gray-400">
                  <Route className="h-3 w-3" />
                  <span>{offer.distance_km} km</span>
                </div>
              )}
            </div>
            
            <div className="flex-1 text-right">
              <p className="text-2xl font-bold text-gray-900">{formatTime(offer.arrival_time)}</p>
              <p className="text-sm text-gray-600">{offer.to_city}</p>
              <p className="text-xs text-gray-400 truncate">{offer.to_station_name}</p>
            </div>
          </div>
        )}

        {/* 4️⃣ Fallback Message - Confidence-based explanation */}
        {offer.is_fallback && (
          <div className="mb-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <div className="flex items-start gap-3">
              <Bus className="h-5 w-5 text-orange-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-gray-900 mb-1">Buses are available on this route</p>
                <p className="text-sm text-gray-600">
                  Live schedules may vary by operator and date. We've shown typical timings and fares based on common services.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Price with Tooltip */}
        <div className="flex items-center justify-between mb-4">
          <div className="relative">
            <div className="flex items-baseline gap-2">
              {/* 6️⃣ Visual Trust Indicator for Price */}
              <span 
                className="text-2xl font-bold text-green-600 cursor-help flex items-center gap-1"
                onMouseEnter={() => setShowFareTooltip(true)}
                onMouseLeave={() => setShowFareTooltip(false)}
              >
                ₹{Math.round(offer.avg_price).toLocaleString('en-IN')}
              </span>
              <span className="text-sm text-gray-500">/ seat</span>
            </div>
            
            {/* 1️⃣ Pricing Clarity - Better label */}
            <p className="text-xs text-gray-500 flex items-center gap-1">
              💰 Estimated Fare • {offer.bus_type_label}
            </p>
            
            {/* 7️⃣ Tooltip on hover */}
            {showFareTooltip && (
              <div className="absolute left-0 top-full mt-2 z-10 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg">
                <p>This is an estimate based on common bus services.</p>
                <p className="mt-1">Final price and seat availability are shown on the booking partner's site.</p>
                <div className="absolute -top-1 left-4 w-2 h-2 bg-gray-900 rotate-45" />
              </div>
            )}
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

        {/* 1️⃣ Pricing Clarity - Additional info text */}
        {isEstimatedResult && !offer.is_fallback && (
          <p className="text-xs text-gray-400 mb-3">
            Estimated fare based on typical services on this route. Actual fares, timings & seats shown on booking partner.
          </p>
        )}

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

        {/* Likely Stops on Route - Expandable Section */}
        {!offer.is_fallback && (
          <LikelyStops 
            fromCity={offer.from_city} 
            toCity={offer.to_city} 
          />
        )}

        {/* 3️⃣ Booking Partners with Improved Button Labels */}
        <div className="border-t pt-4 mt-3">
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
                  getPartnerButtonLabel(partner.name)
                )}
              </button>
            ))}
          </div>
          
          {/* 3️⃣ Helper text below buttons */}
          <p className="mt-2 text-xs text-gray-400">
            You'll be redirected to the operator's website for live availability and booking.
          </p>
        </div>
      </div>
    </div>
  )
}
