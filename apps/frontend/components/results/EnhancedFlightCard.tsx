'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Plane,
  ExternalLink,
  Briefcase,
  UtensilsCrossed,
  Backpack,
  MapPin,
  Clock,
} from 'lucide-react'
import { FlightOffer, Segment } from './ResultCard'
import { formatDuration } from '@/lib/formatters'
import PriceDisplay from '@/components/ui/PriceDisplay'

// Common airline codes to full names mapping
const AIRLINE_NAMES: Record<string, string> = {
  'AI': 'Air India',
  '6E': 'IndiGo',
  'UK': 'Vistara',
  'SG': 'SpiceJet',
  'G8': 'Go First',
  'I5': 'AirAsia India',
  'QP': 'Akasa Air',
  'IX': 'Air India Express',
  '9W': 'Jet Airways',
  'S5': 'Star Air',
  'AA': 'American Airlines',
  'UA': 'United Airlines',
  'DL': 'Delta Air Lines',
  'BA': 'British Airways',
  'LH': 'Lufthansa',
  'EK': 'Emirates',
  'QR': 'Qatar Airways',
  'SQ': 'Singapore Airlines',
  'CX': 'Cathay Pacific',
  'TG': 'Thai Airways',
  'MH': 'Malaysia Airlines',
  'EY': 'Etihad Airways',
  'AF': 'Air France',
  'KL': 'KLM',
}

interface EnhancedFlightCardProps {
  offer: FlightOffer
  badge?: 'best' | 'cheapest' | 'fastest'
  searchParams?: URLSearchParams
}

const BADGE_CONFIG = {
  cheapest: {
    label: 'Cheapest',
    className: 'bg-green-50 text-green-700 border-green-200',
  },
  fastest: {
    label: 'Fastest',
    className: 'bg-purple-50 text-purple-700 border-purple-200',
  },
  best: {
    label: 'Best',
    className: 'bg-blue-50 text-blue-700 border-blue-200',
  },
} as const

// Get full airline name from carrier code or name
function getAirlineName(carrierCode: string, carrierName?: string): string {
  // If we already have a full name (more than 2-3 chars), use it
  if (carrierName && carrierName.length > 3) {
    return carrierName
  }
  // Look up from our mapping
  return AIRLINE_NAMES[carrierCode] || carrierName || carrierCode
}

// Check if arrival is on a different day than departure
function isOvernightFlight(departureTime: string, arrivalTime: string): boolean {
  const depDate = new Date(departureTime).toDateString()
  const arrDate = new Date(arrivalTime).toDateString()
  return depDate !== arrDate
}

// Format stops text correctly (singular/plural)
function formatStopsText(stops: number): string {
  if (stops === 0) return 'Non-stop'
  if (stops === 1) return '1 stop'
  return `${stops} stops`
}

// Calculate layover info between segments
function getLayoverInfo(segments: Segment[]): Array<{ airport: string; city?: string; duration: number }> {
  if (segments.length <= 1) return []
  
  return segments.slice(0, -1).map((seg, idx) => {
    const nextSeg = segments[idx + 1]
    const layoverMs = new Date(nextSeg.departure_time).getTime() - new Date(seg.arrival_time).getTime()
    const layoverMinutes = Math.round(layoverMs / 60000)
    return {
      airport: seg.arrival_airport,
      duration: layoverMinutes,
    }
  })
}

export default function EnhancedFlightCard({
  offer,
  badge,
  searchParams,
}: EnhancedFlightCardProps) {
  const router = useRouter()
  const [showStopDetails, setShowStopDetails] = useState(false)

  const firstSegment = offer.segments[0]
  const lastSegment = offer.segments[offer.segments.length - 1]
  const layovers = getLayoverInfo(offer.segments)
  const isOvernight = isOvernightFlight(firstSegment.departure_time, lastSegment.arrival_time)

  const formatTime = (iso: string) =>
    new Date(iso).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    })

  const handleVendorClick = () => {
    // Navigate to vendors page - user selects vendor there
    // No automatic redirects, no background calls to vendor domains
    const params = new URLSearchParams({
      origin: firstSegment.departure_airport,
      destination: lastSegment.arrival_airport,
      departure_date: firstSegment.departure_time.split('T')[0],
      adults: searchParams?.get('adults') || '1',
      children: searchParams?.get('children') || '0',
      infants: searchParams?.get('infants') || '0',
      price: offer.price.toString(),
      currency: offer.currency || 'INR',
      airline: firstSegment.airline || '',
      flight_number: firstSegment.flight_number || '',
      departure_time: formatTime(firstSegment.departure_time),
      arrival_time: formatTime(lastSegment.arrival_time),
      stops: (offer.segments.length - 1).toString(),
    })
    
    if (searchParams?.get('return_date')) {
      params.set('return_date', searchParams.get('return_date')!)
    }
    
    router.push(`/flights/vendors?${params.toString()}`)
  }

  return (
    <div className="relative bg-white border rounded-lg shadow-sm hover:shadow-md transition">

      {/* BADGE – TOP LEFT */}
      {badge && (
        <span
          className={`absolute top-3 left-3 px-2 py-0.5 text-[11px] font-semibold rounded-md border ${
            BADGE_CONFIG[badge].className
          }`}
        >
          {BADGE_CONFIG[badge].label}
        </span>
      )}

      {/* MAIN ROW */}
      <div className="p-4 flex flex-col sm:flex-row gap-4">

        {/* Airline */}
        <div className="flex items-center gap-3 min-w-[140px]">
          <div className="h-10 w-10 bg-gray-100 rounded flex items-center justify-center">
            <Plane className="h-5 w-5 text-gray-600" />
          </div>
          <div className="font-semibold text-sm truncate">
            {getAirlineName(firstSegment.carrier_code, firstSegment.carrier_name)}
          </div>
        </div>

        {/* Times */}
        <div className="flex-1 flex justify-between text-sm">
          <div>
            <div className="font-bold">
              {formatTime(firstSegment.departure_time)}
            </div>
            <div className="text-xs text-gray-500">
              {firstSegment.departure_airport}
            </div>
          </div>

          <div className="text-center text-xs text-gray-500">
            <div>{formatDuration(offer.total_duration_minutes)}</div>
            {offer.stops === 0 ? (
              <span>Non-stop</span>
            ) : (
              <button
                onClick={() => setShowStopDetails(prev => !prev)}
                className="inline-flex items-center gap-0.5 hover:text-blue-600 transition-colors cursor-pointer"
                aria-expanded={showStopDetails}
                aria-label={`${formatStopsText(offer.stops)}, click for details`}
              >
                <span>{formatStopsText(offer.stops)}</span>
                <ChevronDown 
                  size={12} 
                  className={`transition-transform duration-200 ${showStopDetails ? 'rotate-180' : ''}`}
                />
              </button>
            )}
          </div>

          <div className="text-right">
            <div className="font-bold">
              {formatTime(lastSegment.arrival_time)}
              {isOvernight && (
                <span className="text-xs text-gray-400 ml-1">(+1)</span>
              )}
            </div>
            <div className="text-xs text-gray-500">
              {lastSegment.arrival_airport}
            </div>
          </div>
        </div>

        {/* Price */}
        <div className="text-right">
          <PriceDisplay
            price={offer.price}
            currency={offer.currency}
          />
          <button
            onClick={handleVendorClick}
            className="mt-2 w-full sm:w-auto px-4 py-2 bg-blue-600 text-white rounded text-sm flex items-center justify-center gap-1"
          >
            View Flights
            <ExternalLink size={14} />
          </button>
          {/* Helper text - meta-search redirection */}
          <p className="text-xs text-gray-500 mt-1.5">
            You&apos;ll be redirected to the partner website to complete your booking.
          </p>
        </div>
      </div>

      {/* EXPANDABLE STOP DETAILS */}
      {showStopDetails && offer.stops > 0 && (
        <div 
          className="border-t border-gray-100 bg-gray-50 px-4 py-3 animate-in slide-in-from-top-2 duration-200"
        >
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Stop Details */}
            <div className="flex-1">
              <div className="flex items-center gap-1.5 text-xs font-medium text-gray-700 mb-2">
                <MapPin size={12} />
                <span>Stop Details</span>
              </div>
              <div className="space-y-1.5">
                {layovers.map((layover, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm">
                    <span className="text-gray-600">
                      Stop in: <span className="font-medium">{layover.airport}</span>
                    </span>
                    <span className="text-gray-400">·</span>
                    <span className="flex items-center gap-1 text-gray-500">
                      <Clock size={11} />
                      Layover: {formatDuration(layover.duration)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Amenities (only if data exists) */}
            {(offer.cabin_class || offer.baggage_allowance) && (
              <div className="flex-1 sm:border-l sm:border-gray-200 sm:pl-4">
                <div className="flex items-center gap-1.5 text-xs font-medium text-gray-700 mb-2">
                  <Briefcase size={12} />
                  <span>Flight Details</span>
                </div>
                <div className="flex flex-wrap gap-3 text-sm text-gray-600">
                  {offer.cabin_class && (
                    <span className="flex items-center gap-1.5">
                      <Briefcase size={13} className="text-gray-400" />
                      {offer.cabin_class}
                    </span>
                  )}
                  {offer.baggage_allowance && (
                    <span className="flex items-center gap-1.5">
                      <Backpack size={13} className="text-gray-400" />
                      {offer.baggage_allowance}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
